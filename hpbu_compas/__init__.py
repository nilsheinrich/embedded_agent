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


__title__ = 'hpbu_compas'
__version__ = '0.1'

from .configurator import Config
from .hierarchy import *
from . import functions as fn


"""
    Employ a specialized version of the Hierarchy Predictive Belief Update (HPBU).
    The original HPBU algorithm was published in Kahl & Kopp (2018), with an updated version
    published in the dissertation thesis by Kahl (2020).

    The here provided implementation specifically is meant to be used in the DFG funded SPP Active Self, project COMPAS.
"""