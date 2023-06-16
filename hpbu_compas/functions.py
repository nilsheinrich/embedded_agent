# Copyright 2020 Sebastian Kahl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from numpy.linalg import norm as np_norm
from numpy import dot as np_dot, sqrt as np_sqrt, inf as np_inf
from numpy import log as np_log, sum as np_sum, e as np_e, pi as np_pi, exp as np_exp
from numpy import abs as np_abs, mean as np_mean, var as np_var, max as np_max, clip as np_clip, argmax as np_argmax
from numpy import argmin as np_argmin, cos as np_cos
from scipy.stats import entropy as np_entropy

import numpy as np
from copy import copy
import sys

# from numba import jit, vectorize, void, int8, float64, typeof, types

global smoothing_parameter
smoothing_parameter = 0.0001


def myentropy(P):
    ent = 0.
    for i in P:
        ent -= i * np_log(i)  # to base e
    return ent


def free_energy(P, Q):
    """ see Friston (2012) 
    My interpretation in differences between perception and active inference:
    - In perception, the posterior is the new posterior after perception.
    - In active inference, the posterior is the expected/intended distribution, with the
        new posterior after perception as the prior.
    """
    with np.errstate(all='raise'):
        try:
            # PE = Q - P  # prediction-error
            surprise = myentropy(P)  # np_entropy(P) #  if np_dot(PE, PE) > 0 else 0.
            surprise = surprise if abs(surprise) != np_inf else 0.
            cross_entropy = np_entropy(P, Q)
            cross_entropy = cross_entropy if abs(cross_entropy) != np_inf else 0.
            c_e = 1/(1+np_exp(-4*(cross_entropy - 0.5)))  # should be maxing out at 1
            F = surprise + cross_entropy  # c_e

            return F, surprise, c_e, surprise+cross_entropy
        except Exception as e:
            raise Exception("RuntimeWarning in free_energy(P,Q):", str(e), "#P:", len(P), "#Q:", len(Q))


def get_equal_dist_for_hypos(dpd):
    dist = np.zeros_like(dpd)
    dist[0, :] = 1.0 / dist.shape[0]
    dist = norm_dist(dist, smooth=True)
    
    return dist


def precision(PE):
    """
    Calculate precision as the inverse variance of the updated prediction error.
    return updated precision and updated average_free_energy
    """
    with np.errstate(all='raise'):
        try:
            variance = np_var(PE)  # np_var(PE, ddof=1)  # mad(PE)
            variance = variance if variance > 0.00001 else 0.00001 # so log(var) should max at -5
            pi = np_log(1. / variance)  # should max at 5
            new_precision = 1/(1+np_exp(-(pi - 2.5))) # should be about max. 1

            return pi  # , variance
        except Exception as e:
            raise Exception("RuntimeWarning in precision(PE):", str(e), "PE:", PE) from e


def norm_dist(distribution, smooth=True):
    """
    Normalize distribution, and apply add-one smoothing to leave
    unused probability space.
    """
    global smoothing_parameter

    if smooth:
        add_one_smoothing = smoothing_parameter
        norming_factor = np_sum(distribution[:, 0] + add_one_smoothing) 

        distribution[:, 0] = (distribution[:, 0] + add_one_smoothing) / norming_factor
    else:
        distribution[:, 0] = distribution[:, 0] / np_sum(distribution[:, 0])
    # if smooth:
    #     add_one_smoothing = smoothing_parameter
    #     norming_factor = np_sum(distribution + add_one_smoothing) 

    #     distribution = (distribution + add_one_smoothing) / norming_factor
    # else:
    #     distribution = distribution / np_sum(distribution)
    return distribution


def joint(A, B, smooth=True):
    """
    Joint probability: P(A, B) = P(Ai) + P(Bi) / sum(P(Ai) + P(Bi))
    """
    global smoothing_parameter

    _A = A[A[:, 1].argsort()]
    _B = B[B[:, 1].argsort()]
    joint = copy(_B)

    if smooth:
        add_one_smoothing = smoothing_parameter
        norming_factor = np_sum(_A[:, 0] + _B[:, 0] + add_one_smoothing)
        joint[:, 0] = (_A[:, 0] + _B[:, 0] + add_one_smoothing) / norming_factor

    else:
        joint[:, 0] = _A[:, 0] + _B[:, 0]
        joint[:, 0] = joint[:, 0] / np.sum(joint[:, 0])

    # print("joint probability:\n", A, "\n", B, "\n", joint)

    return joint


def posterior(prior, evidence, smooth=True):
    """
    Calculate the posterior given the prior and the given dpd, normalized by a norming factor.
    """
    global smoothing_parameter

    # P(H|A) = P(H)*P(A|H)/P(A)
    # P(A) = SUM_H(P(H,A)) = SUM_H(P(H)*P(A|H))
    if prior is not None and evidence is not None:

        prior = prior[prior[:, 1].argsort()]
        evidence = evidence[evidence[:, 1].argsort()]

        posterior = copy(prior)
        
        if smooth:
            add_one_smoothing = smoothing_parameter
            norming_factor = np_sum(prior[:, 0] * evidence[:, 0] + add_one_smoothing) 
            # calculate new posterior
            posterior[:, 0] = (prior[:, 0] * evidence[:, 0] + add_one_smoothing) / norming_factor
        else:
            norming_factor = np_sum(prior[:, 0] * evidence[:, 0])
            # calculate new posterior
            posterior[:, 0] = (prior[:, 0] * evidence[:, 0]) / norming_factor
        
        return posterior
    else:
        return None


def kalman_gain(F, pi, oldK=None, gain_gain=0.5):
    """
    Calculate the Kalman gain from free-energy and precision of the layer.

    Examples:
    low pi => steep response in K to small increases in F, max K = 1.0 (strong prediction-error influence)
    high pi => slow response in K to strong increases in F, max K = 0.5 (mostly preserved prior)
    """
    # pi = pi if pi < 5. else 5.  # limit precision variance
    K = F / (F + pi)  # gain factor from free-energy and precision

    if oldK is not None:
        # filter the Kalman Gain over time using a "gain gain" ;)
        # high gain_gain means stronger fluctuations from K
        K, _ = kalman_filter(oldK, K, gain_gain)

    return K


def kalman_filter(prior, observation, K):
    """
    Calculate two iteration kalman filter with given measurement variance.
    The higher the variance the more likely will the prior be preserved.

    Examples:
    low pi => steep response in K to small increases in F, max K = 1.0 (strong prediction-error influence)
    high pi => slow response in K to strong increases in F, max K = 0.5 (mostly preserved prior)

    Returns the posterior estimate.
    """

    # calculate precision from ascending prediction-error
    prediction_error = observation - prior
    xhat = prior + K * prediction_error  # posterior estimate

    return xhat, prediction_error


def multisignal_kalman_filter(prior, observation_gain_tuples):
    posterior = copy(prior)
    for gain, obs in observation_gain_tuples:
        xhat = posterior + gain * (obs - posterior)
        posterior = xhat

    return posterior


def inhibition_belief_update(P, Q, K, tom_Q=None, tom_K=0.5):
    """
    Calculate kalman filter with given free_energy and precision for gain factor.
    The higher the precision the more likely will the prior be preserved.

    P = Prior, Q = Posterior, K = Kalman gain

    Returns the update belief estimate.
    """
    H = copy(P)

    if tom_Q is not None:
        observation_gain_tuples = []

        # add observation gain tuple of current posterior to observation_gain_tuples
        observation_gain_tuples.append((K, Q))
        # add an observation gain tuple for the inferred belief distribution
        observation_gain_tuples.append((tom_K, tom_Q))


        # multisignal kalman update
        H = multisignal_kalman_filter(P, observation_gain_tuples)
        H = norm_dist(H, smooth=True)
    else:
        # simple kalman update
        H, _ = kalman_filter(P, Q, K)
        H = norm_dist(H, smooth=True)

    return H


def gaussian(x, mu, sig):
    """
    Not normally distributed!
    """
    diff = np.array([x - mu])
    # 1/np.sqrt(2*np.pi*sig**2) *  # to make it normally distributed again
    return np_exp((-np_sqrt(np_dot(diff, diff)) ** 2.) / (2. * sig ** 2.))


def prediction_error(P, Q):
    """
    Calculate the size of the prediction error and its variance
    """
    pe = Q - P
    # PE = np_sqrt(np_dot(pe, pe))
    # PE = kl_div(P, Q)
    # print("PE:", PE)
    return pe
