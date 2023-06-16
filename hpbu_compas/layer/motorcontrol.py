# Copyright 2019 Sebastian Kahl
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

""" Rebuild MotorControl
Created on 02.11.2020

@author: skahl
"""

import logging
logger = logging.getLogger("SCL")

from . import register, Layer, fn, Representation, Hypotheses

from copy import copy
from collections import deque
import numpy as np
from time import time



@register
class MotorControl(Layer):
    """ Input-output motor control layer class for predictive processing hierarchy,
    specialized for collecting lower level sensory activity in sequence
    of occurrence and for producing same sensorymotor activity through active inference.
    """


    def __init__(self, name):
        super(MotorControl, self).__init__(name)
        self.type = 'MotorControl'
        self.reset()



    def reset(self):
        super(MotorControl, self).reset()
        # motor control system
        self.alpha = 50  # 25 # 50
        self.beta = 50  # self.alpha / 2  # 6.75  # 4 # 50
        self.phi = 0.  # error
        self.last_position = 0
        # self.joint_vector = None # represents the current max hypothesis
        # self.joint_velocity = None
        self.max_F = 30  # means to trigger action in every update of a 30fps scenario
        self.wait_steps = 0  # counts the steps until an action is triggered
        self.target_precision = 2  # what is the target area around the target?
        self.last_time = time()

        logger.info("(Re-)initialized layer {}".format(self.name))


    def gen_primitives(self):
        self.hypotheses.dpd = np.zeros((61, 2))
        self.hypotheses.dpd[:30, :] = np.array([[1. / 61, -1 * (30 - i)] for i in range(0, 30)])
        self.hypotheses.dpd[30:, :] = np.array([[1. / 61, i] for i in range(0, 31)])
        self.hypotheses.reps = {round(self.hypotheses.dpd[i, 1], 2): Representation(self.hypotheses.dpd[i, 1]) for i in range(0, 61)}

        for idx, dpd_pair in enumerate(self.hypotheses.dpd):
            self.hypotheses.reps[dpd_pair[1]].dpd_idx = idx
        logger.info("{}: Generated primitives:\n{}".format(self.name, list(self.hypotheses.reps.keys())))



    def print_out(self):

        _str_ = self.name
        _str_ += "\nhypotheses ("
        _str_ += str(len(self.hypotheses))
        _str_ += "):\n"
        _str_ += str(self.hypotheses)
        return _str_



    def integrate_evidence(self):
        """ Integrate evidence from sensory activity.
        """

        if self.lower_layer_evidence is not None:
            self.last_position = self.lower_layer_evidence[0]

            if self.intention is None:
                self.intention = 0
            self.phi = self.intention - self.last_position
            
            self.distance = abs(self.phi)

            logger.debug("{}: new MC distance to target: {}".format(self.name, self.distance))
            
            # calculate likelihood of difference
            self.likelihood = self.fit_dist(self.phi)

                

    def fit_dist(self, diff):
        """ Fit the given radians to the distribution of radians.
        """
        dpd = self.hypotheses.dpd
        lh = np.array([[fn.gaussian(diff, i, 1), i] for i in dpd[:, 1]])  # sigma = 0.17
        return fn.norm_dist(lh, smooth=True)



    def td_inference(self):
        """ Integrate influence from higher layers or long range projections.
        """
        # angle possibilities
        if self.hypotheses.dpd is not None and len(self.hypotheses.dpd) > 0:
            if self.long_range_projection is not None:
                """ Here we receive additional information like higher layer signals for intention to act.
                The here received coordinates will define the control problem that needs to be solved by the
                dampened spring system.
                """
                if (LRP := self.long_range_projection.get("intention", False)):
                    self.intention = LRP # np.array([LRP, 0], dtype=np.float32)

                    # update phi
                    self.phi = self.intention - self.last_position

                    # calculate likelihood of difference
                    self.likelihood = self.fit_dist(self.phi)

                    self.td_posterior = fn.norm_dist(self.likelihood, smooth=True)  # fn.joint(self.hypotheses.dpd, self.likelihood, smooth=True)

                    self.distance = abs(self.phi)

                    logger.info("{}: New MC movement goal: {} with distance: {}".format(self.name, self.intention, self.distance))

                if (done := self.long_range_projection.get("done", False)):
                    self.layer_prediction = ["done", False]
                    self.intention = 0  # np.array([0, 0], dtype=np.float32)
                    logger.debug("{}: resetting intention".format(self.name))




    def bu_inference(self):
        """ Calculate the posterior for the sequence layer, based on evidence from
        predicted lower level activity.
        """
        # self.bu_posterior = fn.norm_dist(self.likelihood, smooth=True)
        self.bu_posterior = fn.posterior(self.hypotheses.dpd, self.likelihood, smooth=True)



    def extension(self):
        pass



    def prediction(self):
        """ Motor execution output from a "driven overdampened harmonic oscillator"
        Active inference using the weighted average error-minimizing motor primitive.
        """
        logger.debug("{}: updating MC prediction".format(self.name))

        if self.intention is not None and self.target_precision is not None:
            # retrieve the MAP
            inferred_control = self.hypotheses.max()[1]

            logger.debug("{}: inferred MC control to be used: {}".format(self.name, inferred_control))
            # if self.distance > self.target_precision:
            #     # movement = self.phi_goal - self.joint_vector;
            #     joint_acceleration = self.alpha * (self.beta * inferred_goal - self.joint_velocity)
            #     # integrate acceleration
            #     self.joint_velocity += joint_acceleration
            #     # integrate velocity
            #     self.joint_vector += self.joint_velocity
            #     logger.debug("spring moves to: {}".format(movement))
            t = time()
            delay = t - self.last_time
            self.last_time = t
            logger.debug("update delay: {}".format(delay))

            # check if without moving we are close enough
            # if self.distance <= self.target_precision: 
            #     logger.debug("{}: goal reached!".format(self.name))
            #     # we should stay centered now
            #     self.intention = 0  # np.array([0, 0], dtype=np.float32)
            #     self.layer_prediction = 0
            #     self.phi = 0

            # translate movement strength to movement frequency:
            # -> act if current step fits the frequency
            if inferred_control != 0: # and self.wait_steps >= (self.max_F/abs(inferred_control)):
                if inferred_control < 0:
                    self.layer_prediction = -1
                if inferred_control > 0:
                    self.layer_prediction = 1
                
                # self.wait_steps = 0
            else:
                # self.wait_steps += 1
                self.layer_prediction = 0
        else:
            self.layer_prediction = 0

        logger.debug("{}: movement control: {}".format(self.name, self.layer_prediction))

                



    def receive_evidence(self, evidence):
        """ Overloaded method to receive only sensory data and no representations.
        """
        self.lower_layer_evidence = evidence

