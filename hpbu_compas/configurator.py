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

""" configurator
Creates a config object from loading a json-based configuration file.

Created on 12.12.2019

@author: skahl
"""

import os, logging, sys, json
logger = logging.getLogger("SCL")


class Config(object):
    
    def __init__(self, path, filename=None, read_all=False):
        """ Creates a config object from loading a json-based configuration file.
        """
        self.path = path
        self.config_file = filename

        self.config_storage = None  # holds config structure
        self.layers = []  # holds list of layer configurations
        self.parameters = {}  # holds dictionary of model parameters

        if read_all:
            self.read_config_storage()
            self.config_layer_from_storage()
            self.config_parameters_from_storage()


    def read_config_storage(self):
        """ Read configuration from json file.

        Example config file definition:
        {
            "layers": [
                {
                    "type": "Top",
                    "name": "A",
                    "color": "Blue"
                },
                {
                    "type": "IO",
                    "name": "B",
                    "color": "Red"
                }
            ],
            "parameters": {
                "my_id": "Agent",
                "time_step": 0.01
            }
        }
        """
        if self.config_file is not None:
            try:
                filepath = self.path + os.sep + self.config_file
                logger.info("\t # # # loading config: {}".format(filepath))
                with open(filepath, 'r') as filereader:
                    data_json = filereader.read()
                self.config_storage = json.loads(data_json)
                return self.config_storage
            except IOError as error:
                logger.error(error)
                sys.exit(1)
        else:
            return None


    def config_layer_from_storage(self):
        """ Store layer configuration from storage.
        """
        if self.config_storage is not None and "layers" in self.config_storage:
            layers = self.config_storage['layers']
            for cfg in layers:
                self.layers.append(cfg)
            return True
        else:
            return False


    def config_parameters_from_storage(self):
        """ Store model parameters from storage.
        """
        # configure the following model parameters:
        if self.config_storage is not None and "parameters" in self.config_storage:
            params = self.config_storage["parameters"]

            self.parameters.update(params)
            return True
        else:
            return False