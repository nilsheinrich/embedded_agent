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

""" Compensation
Created on 02.01.2020

@author: skahl
"""

import logging
logger = logging.getLogger("SCL")

from . import register, Layer, fn, Representation, Hypotheses


from copy import copy
import numpy as np


@register
class CompensationLayer(Layer):


    def __init__(self, name):
        super(CompensationLayer, self).__init__(name)
        self.type = 'CompensationLayer'
        self.reset()



    def reset(self):
        super(CompensationLayer, self).reset()

        self.surprise_received = False
        # store lower layer sense of agency estimate
        self.self_estimate = 0.
        # store lower level evidence
        self.last_lower_evidence = None
        self.max_lower_level_hypo = None
        # detector and compensator distributions
        self.error_detector_dpd = None
        self.compensator_dpd = None
        self.max_compensation = None
        self.errorDetected = False
        logger.info("(Re-)initialized layer {}".format(self.name))



    def print_out(self):
        _str_ = self.name
        _str_ += "\nhypotheses ("
        _str_ += str(len(self.hypotheses))
        _str_ += "):\n"
        _str_ += str(self.hypotheses)
        return _str_


    def gen_primitives(self):
        # prep compensation distribution

        self.hypotheses.dpd = np.zeros((61, 2))
        self.hypotheses.dpd[:30, :] = np.array([[1. / 61, -1 * (30 - i)] for i in range(0, 30)])
        self.hypotheses.dpd[30:, :] = np.array([[1. / 61, i] for i in range(0, 31)])
        self.hypotheses.reps = {round(self.hypotheses.dpd[i, 1], 2): Representation(self.hypotheses.dpd[i, 1]) for i in range(0, 61)}

        for idx, dpd_pair in enumerate(self.hypotheses.dpd):
            self.hypotheses.reps[dpd_pair[1]].dpd_idx = idx
        logger.info("{}: Generated primitives:\n{}".format(self.name, self.hypotheses.reps.keys()))



    def integrate_evidence(self):
        """ Integrate evidence from next lower layer.
            Receive vision level distribution and prepare likelihood. 
        """
        if self.intention is None:
            self.intention = 0

        if self.lower_layer_evidence is not None and self.lower_layer_evidence[0] is not None:
            logger.debug("{}: received evidence: {}".format(self.name, self.lower_layer_evidence))
            lower_level_lh = self.lower_layer_evidence[0]
            center_screen_diff = self.lower_layer_evidence[1]
            self.errorDetected, self.likelihood = self.detector(lower_level_lh, center_screen_diff)
            self.last_lower_evidence = copy(lower_level_lh)

            # check if intention was fulfilled
            if not self.errorDetected and self.intention != 0:
                logger.info("{}: {} reached, no more compensation necessary".format(self.name, self.intention))
                self.intention = 0
                self.max_compensation = 0

            # likelihood => detected error
            self.compensator_dpd = self.compensator()


    def detector(self, evidence, target=None):
        """ Simple detector that represents the difference between the predicted and actual movements
        """
        diff = 0

        # if evidence is not yet available, assume straight downward movement
        if evidence is not None:
            max_evidence = evidence[fn.np_argmax(evidence[:, 0]), 1]  # get the max evidence movement
        else:
            max_evidence = 0  # straight downward movement
        
        # targeting the intention!
        # use diff later
        diff = max_evidence - self.intention

        # ignore differences lesser than 1
        # if diff <= 1:
        #     # ignore diff, so diff=0
        #     diff = 0
        #     self.error_detector_dpd = np.array([[fn.gaussian(diff, i, 1), i] for i in self.hypotheses.dpd[:, 1]])
        # else:
        # use real diff here:
        self.error_detector_dpd = np.array([[fn.gaussian(diff, i, 1), i] for i in self.hypotheses.dpd[:, 1]])

        logger.debug("{}: diff detected: {} ({} - {})".format(self.name, diff, max_evidence, self.intention))  # , "error detected:", self.error_detector_dpd)

        # or return here, compensating
        return diff != 0, copy(self.error_detector_dpd)
        

    def compensator(self):
        """ Given the intended movement target, the precision-weighted error (P), 
        here, the weighted error is compensated to reach the movement target.
        """
        if self.errorDetected:
            max_error = self.error_detector_dpd[fn.np_argmax(self.error_detector_dpd[:, 0]), 1]  # self.hypotheses.max()
            compensation = -max_error  # self.PE.precision * max_error
            compensator_dpd = np.array([[fn.gaussian(compensation, i, 1), i] for i in self.hypotheses.dpd[:, 1]])
        else:
            max_error = 0
            compensator_dpd = self.hypotheses.dpd

        # compensation
        self.max_compensation = compensator_dpd[fn.np_argmax(compensator_dpd[:, 0]), 1]  # compensation magnitude factor

        if max_error != 0:
            logger.debug("{}: max error: {}".format(self.name, compensation))

        return compensator_dpd


    def td_inference(self):
        """ Receive and integrate higher layer and long range projections.
        """
        if self.long_range_projection is not None:
            logger.debug("long range projection: {}".format(self.long_range_projection))
            if "intention" in self.long_range_projection:
                rel_target = self.long_range_projection["intention"]
                # get movement direction from movement target vector
                self.intention = rel_target[0] # focus on x-axis only
                logger.debug("{}: received intention: {}".format(self.name, self.intention))
                
                if self.last_lower_evidence is not None:

                    # include compensation bias from cognitive control layer (CCL)
                    if "compensation bias" in self.long_range_projection:
                        # translate and fit into discrete probability distribution
                        translated_bias = 30 * self.long_range_projection["compensation bias"]
                        self.td_posterior = fn.norm_dist(np.array([[fn.gaussian(translated_bias, i, 1), i] for i in self.hypotheses.dpd[:, 1]]))
                    else:
                        # fall back to top-most layer behavior
                        self.td_posterior = copy(self.hypotheses.dpd)

                    # seems this has arrived a bit early in the agent's life cycle. Let's still store it.
                    self.errorDetected, self.likelihood = self.detector(self.last_lower_evidence)
                    self.compensator_dpd = self.compensator()

            if "surprise" in self.long_range_projection:
                logger.debug("{}: Received delay-surprise signal from level: {}".format(self.name, self.long_range_projection["surprise"]))
                self.surprise_received = True

            if "crash" in self.long_range_projection and self.long_range_projection["crash"]:
                logger.debug("{}: Received crash-signal from environment.".format(self.name))
                self.likelihood = fn.get_equal_dist_for_hypos(self.hypotheses.dpd)
                self.td_posterior = fn.posterior(self.hypotheses.dpd, self.likelihood)

            # receive information about an intended action's completion
            if "done" in self.long_range_projection:
                self.action_done = True
                self.surprise_received = True
                self.intention = 0

        # elif self.higher_layer_prediction is not None:
        #     self.log(4, "higher layer projection:", self.higher_layer_prediction)
        #     higher_layer = copy(self.higher_layer_prediction)
        #     P_C = higher_layer[0]  # higher layer posterior distribution
        #     matrix = higher_layer[1]  # likelihood matrix

        #     # perform top-down inference from mixture of experts
        
        #     """ correct td_posterior from P(S_C, C), including the normalized P(S|C_i) """
        #     # P(S_C, C) = sum_j( P(S_i|C_j) P(C_j) )
        #     self.td_posterior = mixture_experts(self.hypotheses.dpd, P_C, matrix, smooth=True)

        #     self.log(4, "updated top-down posterior from higher layer:\n", self.td_posterior)



    def bu_inference(self):
        """ Calculate the posterior for the sequence layer, based on evidence from
        predicted lower level activity.
        """
        if self.hypotheses.dpd is not None and len(self.hypotheses.dpd) > 0:
            if self.likelihood is not None:
                # logger.debug("evidence: {}".format(self.likelihood))
                self.bu_posterior = fn.posterior(self.hypotheses.dpd, self.likelihood, smooth=True)
                # logger.debug("updated bottom-up posterior:\n{}".format(self.bu_posterior))



    def extension(self):
        """ Decide on and do hypothesis extension and
        decide on evidence for next higher layer.
        """
        if self.likelihood is not None and self.max_compensation is not None:
            # update the self-estimate as a precision-weighted linear dynamic update on the intention likelihood 
            int_idx = self.hypotheses.reps[self.max_compensation].dpd_idx
            # self.self_estimate = (1.0 - self.K)
            self.self_estimate += self.K * (self.likelihood[int_idx, 0] - self.self_estimate)

            logger.debug("Updated self estimate to {} for intention {}".format(self.self_estimate, self.max_compensation))
            self.layer_evidence = [self.hypotheses, self.self_estimate]



    def prediction(self):
        """ Decide on predicted next lower layer activity in best predicted sequence.
        """
        if self.errorDetected and self.max_compensation is not None:
            # if no intention prediction available, just commit to the available information
            logger.debug("{}: compensation: {}".format(self.name, self.max_compensation))
            self.layer_long_range_projection = {}
            self.layer_long_range_projection["MC"] = {"intention": self.max_compensation}
            self.layer_long_range_projection["Vision"] = {"intention": self.max_compensation}

        self.layer_prediction = self.hypotheses.dpd

