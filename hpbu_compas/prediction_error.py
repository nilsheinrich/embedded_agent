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

""" PredictionError
Created on 17.06.2019

@author: skahl
"""


from collections import deque

from .functions import *
# from .representations import *


class PredictionError(object):
    """
    Represent the layer prediction error and its statistics
    """

    def __init__(self):
        self.PE = 0.  # current prediction-error
        self.mean_PE = 0.  # current mean prediction-error
        self.var_PE = 0.  # current variance over prediction-errors
        self.transient_PE = deque(maxlen=30)

        self.threshold = 0.
        self.precision = 1.
    
    def new(self, surprise, P, Q):
        self.PE = prediction_error(P, Q)  # surprise
        
        # calculate new statistics
        if len(self.transient_PE) > 1:
            self.mean_PE = np_mean(self.transient_PE)
            self.var_PE = np_var(self.transient_PE)
        # before adding the new PE, leaving it effectively out
        self.transient_PE.append(self.PE)
        self.threshold = self.mean_PE + self.var_PE
        # calculate precision of the flattened array
        self.precision = precision(self.transient_PE)

    def is_surprising(self):
        """
        decide if the current prediction-error is surprising,
        given the history of prediction-errors and the current sensory precision.

        pi = precision
        """
        self.threshold = self.mean_PE + self.var_PE
        return self.PE > self.threshold

    def some_surprise(self):
        if len(self.transient_PE) > 1:
            # print(self.PE, '>', self.transient_PE[-2])
            return self.PE > self.transient_PE[-2]
        else:
            return False

    def clear(self):
        self.transient_PE.clear()  # empty the deque
        self.PE = 0.  # current prediction-error
        self.mean_PE = 0.  # current mean prediction-error
        self.var_PE = 0.  # current variance over prediction-errors
        self.threshold = 0.

    def __str__(self):
        return str(self.PE) + ' > ' + str(self.threshold)