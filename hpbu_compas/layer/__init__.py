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


""" layer
Represents the base class for layers of the agent's processing hierarchy.

Created on 12.12.2019

@author: skahl
"""

import sys, logging
from collections import deque
from copy import copy
import numpy as np

from .. import functions as fn

from ..prediction_error import PredictionError
from .representations import Hypotheses, Representation


logger = logging.getLogger("SCL")

classes = {}
def register(cls):
    logger.info("registering {}".format(cls.__name__))
    classes[cls.__name__] = cls
    return cls


class Layer(object):

    def __init__(self, name):
        # layer identity and parameters
        self.name = name
        self.enabled_processing = True
        self.params = {}

        # layer state
        self.hypotheses = Hypotheses()
        self.reset()


    def reset(self):

        # distributions, inferences, and statistics
        self.td_posterior = None  # posterior calculated from top-down projection
        self.bu_posterior = None  # posterior calculated from bottom-up evidence

        self.PE = PredictionError()
        self.K = 0.5  # layer Kalman gain

        self.free_energy = 0.1  # layer free energy calculated between available posteriors
        self.transient_PE = deque(maxlen=20)  # store past prediction-error
        self.likelihood = None  # calculated likelihood distribution given the bottom-up evidence
        self.self_estimate = 0.  # sense of agency estimate for current production
        self.intention = None  # intention is set by long range projections

        # convenient variables
        self.best_hypo = None  # currently best hypothesis
        self.last_t_hypotheses = None

        # layer communication
        self.higher_layer_prediction = None  # in
        self.higher_layer_pruning = None  # in

        self.layer_evidence = None  # out
        self.layer_prediction = None  # out
        self.layer_new_hypo = None  # out
        self.layer_long_range_projection = None  # out

        self.lower_layer_hypos = None  # to be initialized
        self.lower_layer_evidence = None  # initialized
        self.lower_layer_new_hypo = None  # in
        self.long_range_projection = None  # in
        logger.info("(Re-)initialized base Layer")


    def __repr__(self):
        return "Layer {}".format(self.name)


    def set_parameters(self, parameters):
        """ Initialize layer parameters from configuration.
        """
        self.params = parameters
    

    def prediction(self):
        """ Sample new prediction based on updated state.
        Return prediction for sending.
        """
        raise NotImplementedError("Should have implemented this")


    def integrate_evidence(self):
        """ Receive and integrate the evidence with previous evidence.
        """
        raise NotImplementedError("Should have implemented this")


    def td_inference(self):
        """ Receive and integrate higher layer and long range projections.
        """
        raise NotImplementedError("Should have implemented this")


    def bu_inference(self):
        """ Infer new bottom-up posterior based on prior and evidence.
        """
        raise NotImplementedError("Should have implemented this")


    def extension(self):
        """ Decide on and do hypothesis extension and
        decide on evidence for next higher layer.
        """
        raise NotImplementedError("Should have implemented this")


    def receive_prediction(self, prediction):
        """ Receive prediction from next higher layer.
        """
        self.higher_layer_prediction = prediction[0]
        self.higher_layer_K = prediction[1]


    def receive_evidence(self, evidence):
        """ Receive evidence from next lower layer.
        """
        self.lower_layer_evidence = evidence[0]
        self.lower_layer_new_hypo = evidence[1]
        # self.lower_layer_K = evidence[2]


    def receive_long_range_projection(self, projection):
        """ Receive long range projections from other sources.
        """
        self.long_range_projection = projection


    def receive_lower_level_hypos(self, ll_hypos):
        """ Inform level about lower level's hypotheses
        """
        self.lower_layer_hypos = ll_hypos


    def send_level_hypos(self):
        """ Send level's hypos to next higher level
        """
        return self.hypotheses


    def send_prediction(self):
        """ Send prediction for next lower layer.
        """
        return [self.layer_prediction, self.K]


    def send_evidence(self):
        """ Send evidence for next higher layer.
        """
        return [self.layer_evidence, self.layer_new_hypo]


    def send_long_range_projection(self):
        """ Send long range projection to another layer by name.
        """
        return self.layer_long_range_projection


    def clean_up(self):
        """ Clean up used object attributes after hierarchy update.

        WARNING: Messing with these could have unforseen consequences!
        """
        # remote references
        self.higher_layer_prediction = None
        self.long_range_projection = None
        self.lower_layer_new_hypo = None
        self.lower_layer_evidence = None

        # local attributes
        # if self.params["self_supervised"]:
        # self.bu_posterior = None  
        self.td_posterior = None  
        self.likelihood = None
        # self.best_hypo = None
        # self.lower_layer_hypos = None
        # self.layer_evidence = None
        # self.layer_LH = None  # otherwise updated dependend on word length won't work
        self.layer_prediction = None
        # self.layer_new_hypo = None
        # self.layer_long_range_projection = None


    def finalize(self):
        self.clean_up()


    def update(self):
        """ All the prediction-error handling logic.
        """

        # in order to disable processing from this layer and above, set this to False
        if not self.enabled_processing:
            return

        # store current hypothesis for later comparison
        self.last_t_hypotheses = copy(self.hypotheses.dpd)

        # incorporate new evidence
        self.integrate_evidence()

        if self.higher_layer_prediction is not None \
                or self.long_range_projection is not None:
            # incorporate higher layer and long distance projections
            self.td_inference()  # calculate the top-down posterior
        
        # calculate inference
        if len(self.hypotheses.reps) > 0 and\
                self.likelihood is not None and\
                (self.lower_layer_evidence is not None or
                    self.lower_layer_new_hypo is not None):
            # Bayesian update of posterior distribution
            self.bu_inference()  # calculate the bottom-up posterior

        if len(self.hypotheses.reps) > 1 and self.td_posterior is not None and self.bu_posterior is not None:
            """ top-down and bottom-up posteriors are available, 
            so we perform a full update
            """

            # calculate free-energy and K
            if self.higher_layer_prediction is not None or\
                    self.long_range_projection is not None or\
                    self.lower_layer_evidence is not None or\
                    self.lower_layer_new_hypo is not None:

                # active inference: top-down drives action
                prior = self.td_posterior[:, 0]    # driving signal
                post = self.bu_posterior[:, 0]     # adapted feedback

                # logger.debug("\tbu:\n{}\n\ttd:\n{}".format(self.bu_posterior, self.td_posterior))

                try:
                    # calculate free energy
                    F = fn.free_energy(P=prior, Q=post)
                    # print("intention:", self.intention, "post:", post.shape, "prior:", prior.shape)
                    self.free_energy = F[0]
                    self.PE.new(surprise=F[3], P=prior, Q=post)
                    # self.log(3, "max for driving signal:", max_p, "posterior:", max_q)
                    logger.debug("{}: free energy: {} surprise: {} cross-entropy: {}".format(self.name, self.free_energy, F[1], F[2]))

                    # check if all posteriors add up to one, and tell warning if not
                    sum_bu = fn.np_sum(post)
                    if sum_bu > 1.1 or sum_bu < 0.9:
                        logger.error("bu_posterior not normalized: {}".format(sum_bu))

                    sum_td = fn.np_sum(prior)
                    if sum_td > 1.1 or sum_td < 0.9:
                        logger.error("td_posterior not normalized: {}".format(sum_td))

                    hl_k = self.K

                    logger.debug("{}: calculating belief update with K = {}".format(self.name, hl_k))
                    # we are interested in the top-down adaptation
                    self.hypotheses.dpd = fn.inhibition_belief_update(self.td_posterior, self.bu_posterior, hl_k)

                    # update dpd_idx mapping
                    self.hypotheses.update_idx_id_mapping()
                except Exception as e:
                    logger.error(str(e))
                    sys.exit(1)

            logger.debug("{}: full belief update activity".format(self.name))

        elif len(self.hypotheses.reps) > 1 and self.bu_posterior is not None:
            """ default free energy if no distribution for comparison is given, 
            so we compare what we have with the last posterior
            """
            logger.debug("{}: calculating partial free energy update".format(self.name))
            post = self.bu_posterior[:, 0]
            prior = self.hypotheses.dpd[:, 0]

            # logger.debug("{}:\n\tbu:\n{}\n\ttd:\n{}".format(self.name, self.bu_posterior, self.hypotheses.dpd))

            # calculate free energy
            F = fn.free_energy(P=prior, Q=post)
            self.free_energy = F[0]
            self.PE.new(surprise=F[0], P=prior, Q=post)
            logger.debug("{}: free energy: {} surprise: {} cross-entropy: {}".format(self.name, self.free_energy, F[1], F[2]))

            self.hypotheses.dpd = fn.inhibition_belief_update(self.hypotheses.dpd, self.bu_posterior, self.K)
            # self.hypotheses.dpd = self.bu_posterior

            # update dpd_idx mapping
            self.hypotheses.update_idx_id_mapping()
            # self.log(1, self.hypotheses.max())
            logger.debug("{}: partial belief update activity".format(self.name))

        elif len(self.hypotheses.reps) > 1 and self.td_posterior is not None:
            """ default free energy if no distribution for comparison is given, 
            so we compare what we have with the last posterior
            """
            logger.debug("{}: calculating partial free energy update".format(self.name))

            logger.debug("{}: calculating belief update with K = {}".format(self.name, self.K))
            prior = self.td_posterior[:, 0]
            post = self.hypotheses.dpd[:, 0]
            # logger.debug("\tbu:\n{}\n\ttd:\n{}".format(self.hypotheses.dpd, self.td_posterior))

            # calculate free energy
            F = fn.free_energy(P=prior, Q=post)
            self.free_energy = F[0]
            self.PE.new(surprise=F[0], P=prior, Q=post)
            logger.debug("{}: free energy: {} surprise: {} cross-entropy: {}".format(self.name, self.free_energy, F[1], F[2]))

            self.hypotheses.dpd = fn.inhibition_belief_update(self.td_posterior, self.hypotheses.dpd, self.K)
            # self.hypotheses.dpd = self.td_posterior

            # update dpd_idx mapping
            self.hypotheses.update_idx_id_mapping()
            # self.log(1, self.hypotheses.max())
            logger.debug("{}: partial belief update activity".format(self.name))
        else:
            logger.debug("{}: no belief update!".format(self.name))
        
        """ Update Kalman Gain """
        # self.set_intention_dependent_kalman_gain()
        # self.set_variable_kalman_gain()
        self.K = fn.kalman_gain(self.free_energy, self.PE.precision)
    
        # apply extensions
        self.extension()

        # new prediction
        # if self.hypotheses.dpd.shape[0] > 0:
        self.prediction()


    def set_intention_dependent_kalman_gain(self):
        """ fixate K depending on intention setting.
        belief' = td_posterior + K * (bu_posterior - td_posterior)
        """
        if "bias_gain" in self.params:
            gain_bias = self.params['bias_gain']
        else:
            gain_bias = 0.5

        if self.intention is None:
            # during PERCEPTION
            self.K = kalman_gain(self.free_energy, self.PE.precision, gain_bias, gain_gain=0.5)

            # if self.name in ["Realizations", "Schm", "Seq"]:
            #     # increase Kalman Gain to make these layer susceptible to evidence
            #     self.K = gain_bias # 0.9
            # elif self.name in ["Goals", "MC", "Vision"]:
            #     # decrease Kalman Gain for these layers
            #     self.K = 1 - gain_bias # 0.1
            
            # if self.name == "Vision":
            #     self.K = 1.0
        elif self.intention is not None:
            # during PRODUCTION

            # if self.name == "Compensation":
            #     gain_bias = 0.9

            self.K = kalman_gain(self.free_energy, self.PE.precision, gain_bias, gain_gain=0.5)

            # if self.name in ["Goals", "Schm", "Seq"]:
            #     # decrease Kalman Gain for these layers to be less susceptible to evidence
            #     self.K = 1 - gain_bias # 0.1
            # elif self.name in ["Realizations", "Vision", "MC"]:
            #     # increase Kalman Gain for these layers
            #     self.K = gain_bias # 0.9

        
        logger.debug("{}: K = {} for {}".format(self.name, self.K, self.name))



from .motorcontrol import MotorControl
from .visionlayer import VisionLayer
from .compensation import CompensationLayer