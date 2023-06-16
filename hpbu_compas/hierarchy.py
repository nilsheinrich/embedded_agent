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


""" hierarchy
Holds the hierarchy that structures the updating of all layers of the model.
Also handles communication between the model and the environment.

Created on 12.12.2019

@author: skahl
"""

# system modules
from collections import deque
import sys
import os
from time import time, sleep
import logging
# own modules
from .configurator import Config
from .layer import classes, Layer

import numpy as np


logger = logging.getLogger("SCL")


class Hierarchy(object):

    def __init__(self, config):
        """ Initialize the hierarchy by a config object, containing name and type dictionaries.
        """

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # main structures
        self.config = config
        self.layers = []
        self.layername_idx_dict = {}
        # layer references and state
        self.io_layer_names = ["Vision", "MC"]
        self.input = {}
        self.last_layer = None  # remember the layer that was last updated
        self.queue_long_range_projection = deque(maxlen=100)

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # parameters
        self.my_id = self.config.parameters['my_id'] 

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # apply layer config
        for config_line in self.config.layers:
            logger.debug("config line: {}".format(config_line))
            layer = self.layer_factory(config_line)

            if layer is not None:
                # remember index position of layer list
                self.layername_idx_dict[config_line["name"]] = len(self.layers)
                self.layers.append(layer)
            else:
                logger.error("Something went wrong in the layer factory: layer type is not known!")

    def get_layer(self, name):
        """ Access layer in layers list.
        """
        if name in self.layername_idx_dict:
            return self.layers[self.layername_idx_dict[name]]
        else:
            raise AttributeError("No such layer: {}".format(name))

    def set_layer(self, name, value):
        """ Access layer in layers list.
        """
        if name in self.layername_idx_dict:
            self.layers[self.layername_idx_dict[name]] = value
        else:
            raise AttributeError("No such layer: {}".format(name))

    def layer_factory(self, layer_config):
        """ Allows to instantiate layer objects for registered layer classes
        from their configured class names.
        """

        if layer_config["type"] in classes:
            layer = classes[layer_config["type"]]

            return layer(name=layer_config["name"])
        else:
            return None

    def update(self, _input=None, _top_down=None):
        """ The full hierarchy update routine.
        This is a "prediction-first" update, so we update with the top most layer first,
        traversing the hierarchy down until we reach the bottom most layer.

        Send input via _input dictionary using {"vision": your_visual_input}
        
        returns model prediction.
        """

        # collect SoC and maximum compensation value from compensation layer
        soc = 0.
        compensation = 0.

        # set input
        self.input = _input
        self.top_down = _top_down

        # per-layer pre-update cleanup
        for layer in self.layers:
            layer.clean_up()

        # prep for outside influence
        last_layer = self.get_top_down_layer()
        if last_layer is not None:
            prediction = last_layer.send_prediction()
        else:
            prediction = [None, None]

        # Check queue for outside long-range projection input
        long_range_projection = self.get_long_range_projection()

        if long_range_projection.get("Compensation", False):
            logger.debug("new cognitive control information: {}".format(long_range_projection.get("Compensation")))

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # update step: traverse the hierarchy in order (top-down)
        for i, layer in enumerate(self.layers):
            logger.debug("Updating layer: {}".format(layer))
            
            # get next lower layer
            next_layer = self.get_next_layer(i)  # returns None at the bottom-most layer

            """ receive top-down and long-range projections """
            # receive top-down information from next higher layer or external source
            layer.receive_prediction(prediction)
            # receive long-range projection for this layer
            if (lrp := long_range_projection.get(layer.name, False)):
                layer.receive_long_range_projection(lrp)
            """ receive bottom-up projections """
            if next_layer is not None:
                # receive separate bottom-up hypothesis space, if available
                next_level_hypos = self.get_layer(next_layer.name).send_level_hypos()
                layer.receive_lower_level_hypos(next_level_hypos)
            # receive bottom-up evidence or input
            next_level_evidence = self.get_next_layer_evidence(i)
            # logger.debug("{}: next layer ({}) evidence {}".format(layer.name, next_layer, next_level_evidence))
            layer.receive_evidence(next_level_evidence)

            """ run layer update """
            # update layer
            layer.update()

            """ retrieve updated predictions and long-range projections for the layer next in line """
            # send prediction to next lower layer
            prediction = layer.send_prediction()
            # prepare long range projections
            self.set_long_range_projection(layer.send_long_range_projection())

            """ retrieve SoC from Compensation layer specifically """
            if layer.name == "Compensation":
                # if layer is compensation layer, retrieve current SoC value
                soc = layer.self_estimate 
                next_level_evidence = next_level_evidence[0]
                if layer.max_compensation is not None:
                    compensation = layer.max_compensation / 30.  # normalize to -1 to 1

            # set new top-down layer
            self.last_layer = layer 

        return prediction[0], next_level_evidence, soc, compensation  # (prediction, feedback, soc, max_compensation)

    def get_info(self, layer_name):
        """ Retrieve information from the given layer and return them as a dictionary.

        Returned information are the layer's K, SoC (if available) and F
        """ 
        if layer_name in self.layername_idx_dict:
            layer = self.layers[self.layername_idx_dict[layer_name]] 
            return {
                'K': layer.K,
                'precision': layer.PE.precision,
                'F': layer.free_energy,
                'SoC': layer.self_estimate
            }
        else:
            return {}

    def set_long_range_projection(self, _input):
        """ Set a specific input to a layer.
        Input expects a list of [layer_name, influence].
        """
        if _input is not None:
            if len(_input) > 0:
                self.queue_long_range_projection.appendleft(_input)
            else:
                logger.error("A list is expected with structure [layer_name, influence].")

    def get_long_range_projection(self):
        long_range_projection = {}
        if len(self.queue_long_range_projection) > 0:
            _lr = self.queue_long_range_projection.pop()
            for target, com in _lr.items():
                long_range_projection[target] = com
        return long_range_projection

    def get_top_down_layer(self):
        """ Receive influence from cognitive control layer.
        """
        if self.top_down is not None:
            return self.top_down
        else:
            return None

    def get_next_layer(self, index):
        """ Return the next layer in the hierarchy.
        """
        if index < len(self.layers)-1 and index >= 0:
            return self.layers[index+1]
        else:
            None

    def get_next_layer_hypos(self, index):
        """ Return the next layer's hypotheses.
        """
        if index < len(self.layers)-1 and index >= 0:
            return self.layers[index+1].send_level_hypos()
        else:
            return None
    
    def get_next_layer_evidence(self, index):
        """ Return the next layer's evidence output.

        If index outside of known layers, return input.
        """
        if self.layers[index].name in self.io_layer_names and self.input is not None:
            return self.input.get(self.layers[index].name, None)
        elif index < len(self.layers):
            return self.layers[index+1].send_evidence()
        else:
            return None

    def finalize(self):
        """ Call finalize method for each layer.
        """
        for layer in self.layers:
            layer.finalize()
        
