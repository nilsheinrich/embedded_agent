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

""" VisionLayer
Created on 15.08.2017

@author: skahl
"""

import logging
logger = logging.getLogger("SCL")

from . import register, Layer, fn, Representation, Hypotheses

from copy import copy
from collections import deque
import numpy as np

@register
class VisionLayer(Layer):
    """ Visual input layer class for predictive processing hierarchy,
    specialized for collecting lower level sensory activity in sequence
    of occurrence and for producing same sensorymotor activity through active inference.
    """


    def __init__(self, name):
        super(VisionLayer, self).__init__(name)
        self.type = 'VisionLayer'

        # minimally: r=11, theta=9
        # last: 19, 13

        # self.oculocentric_coordinates = define_coordinate_system(r=30, theta=29)
        self.reset()



    def reset(self):
        super(VisionLayer, self).reset()
        # store last temporal delta between divergences
        self.delta_t = 0.
        # isDrawing estimate
        self.isDrawing = True
        # store current coordinate
        # self.cur_coordinate = np.array([0., 0.])
        self.last_coordinate = np.array([0., 0.])
        # self.phi_history = deque(maxlen=5)
        # store intentionality information
        self.last_intention = None
        self.step_counter = 0

        # follow-through necessacities
        self.allow_follow_through = False
        self.prior_distance_to_target = None
        self.will_probably_reach_target = False
        self.follow_through_factor = 0.3

        logger.info("(Re-)initialized layer {}".format(self.name))



    def gen_primitives(self):
        # prep angle distribution
        # distribution based on angular primitive resolution of 360/20 = 20 degrees, or ~0,314 radians
        # decreased angular primitives to 180 / 20 = 20 degrees, or 

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
            self.delta_t += self.lower_layer_evidence[1]

            if self.lower_layer_evidence[0] is not None:
                # ignore y offset completely
                evidence_offset = np.array([self.lower_layer_evidence[0][0], 0], dtype=np.float32)

                self.isDrawing = True
                # phi is the vector between last and current coordinate
                # self.cur_coordinate += copy(evidence_offset)
                self.last_coordinate = copy(evidence_offset)
                diff = self.last_coordinate[0]  # lower layer evidence is also a coordinate, focus on x-coordinate

                # fit the angle to the hypotheses distribution
                self.likelihood = self.fit_dist(diff)  # lh to be joined with prior distribution

                logger.debug("{}: movement-diff now: {} with fit: {}".format(self.name, diff, self.likelihood[fn.np_argmax(self.likelihood[:, 0])]))


            elif self.lower_layer_evidence[1] is not None:
                # good signal for a reset
                # self.cur_coordinate = np.array([0., 0.])
                self.last_coordinate = np.array([0., 0.])




    def fit_dist(self, diff):
        """ Fit the given radians to the distribution of radians.
        """
        dpd = self.hypotheses.dpd
        lh = np.array([[fn.gaussian(diff, i, 1), i] for i in dpd[:, 1]])  # sigma = 0.17
        return lh



    def td_inference(self):
        """ Integrate influence from higher layers or long range projections.
        """
        # angle possibilities
        if self.last_coordinate is not None and self.hypotheses.dpd is not None and len(self.hypotheses.dpd) > 0:

            if self.long_range_projection is not None:
                """ These coordinates will get send from the motorcontrol for vision to verify that
                it has indeed correctly moved.
                """
                if "intention" in self.long_range_projection:
                    LRP = self.long_range_projection["intention"]

                    # phi = np.array([np.cos(LRP), np.sin(LRP)])
                    phi = LRP
                    # set intention to check up on in case of LRP from proprioception
                    # self.intention_check = [phi]
                    logger.info("{}: New primed target: {}".format(self.name, phi))

                    self.intention = phi

                    # fit the angle to the hypotheses distribution
                    likelihood = self.fit_dist(phi)
                    # self.td_posterior = posterior(self.hypotheses.dpd, likelihood, smooth=True)
                    self.td_posterior = fn.norm_dist(likelihood, smooth=True)


                elif "done" in self.long_range_projection:
                    if self.long_range_projection["done"] == "Seq":
                        logger.debug("{}: Received surprise signal from Sequence layer".format(self.name))
                        # self.cur_phi_magnitude = None
                    else:
                        # self.intention_check = []
                        self.intention = None
                        self.delta_t = 0.

            elif self.higher_layer_prediction is not None:
                # logger.debug("higher layer projection: {}".format(self.higher_layer_prediction))
                higher_layer = copy(self.higher_layer_prediction)

                if self.hypotheses.dpd.shape[0] == higher_layer.shape[0]:
                    # self.td_posterior = posterior(self.hypotheses.dpd, higher_layer, smooth=True)
                    # self.td_posterior = norm_dist(higher_layer, smooth=True)
                    self.td_posterior = fn.joint(self.hypotheses.dpd, higher_layer, smooth=True)
                else:
                    logger.debug("{}: Incompatible higher layer projection: {} to {}".format(self.name, higher_layer.shape[0], self.hypotheses.dpd.shape[0]))


    def bu_inference(self):
        """ Calculate the posterior for the sequence layer, based on evidence from
        predicted lower level activity.
        """
        # self.bu_posterior = fn.norm_dist(self.likelihood, smooth=True)
        self.bu_posterior = fn.posterior(self.hypotheses.dpd, self.likelihood, smooth=True)



    def extension(self):
        """ No extension in this layer. Primitives are fixed.

        Check if new best hypothesis should be found and if there is surprisal in the currently best_hypo,
        send the current coordinate to next layer as a "waypoint" if input was surprising. (segmentation by Zachs, etc)
        """

        if self.likelihood is not None and self.hypotheses is not None:
            logger.debug("updating Vision extension")
            # max_id = self.hypotheses.max()[1]
            # cur_best_hypo = self.hypotheses.reps[max_id]

            # calculate necessary difference towards center of screen:
            center_diff = -self.last_coordinate[0]

            # do not care about surprise here
            self.layer_evidence = [self.hypotheses.dpd, center_diff]
            



    def prediction(self):
        """ Decide on active inference on sensorimotor activity.
        """
        pass


    def receive_evidence(self, evidence):
        """ Overloaded method to receive only sensory data and no representations.
        """
        self.lower_layer_evidence = evidence

