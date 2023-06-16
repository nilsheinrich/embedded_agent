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

""" Representations
Created on 21.08.2017

@author: skahl
"""
from collections import deque

from copy import copy


import numpy as np
from numpy import sqrt as np_sqrt, dot as np_dot


class Representation(dict):
    """ Basic representation class, accessible as dictionary.
    """

    def __init__(self, idx):
        self.id = idx
        self.dpd_idx = 0  # make the index to ID pairing bidirectional


    def serialize(self):
        D = {}
        D["id"] = self.id
        D["dpd_idx"] = self.dpd_idx
        return D


    def deserialize(self, D, deserialized_lower_layer=None):
        self.id = D["id"]
        return self


    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


    def __setattr__(self, name, value):
        self[name] = value


    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


    def __repr__(self):
        return str(self.id)






# class Cluster(Representation):
#     """ Cluster specification of the representation class.
#     """
#     def __init__(self, idx):
#         super(Cluster, self).__init__(idx)

#         self.seqs = []
#         self.prototype = None
#         self.avg_sim = 0.
#         self.var_sim = 0.
#         self.similarity_matrix = None
#         # self.bins = {'coords': [], 'timings': []}  # will store collections.Counter and defaultdict(list)


#     def __repr__(self):
#         return str([seq['id'] for seq in self.seqs])


#     def serialize(self):
#         D = {}
#         D["super"] = super(Cluster, self).serialize()
#         D["seqs"] = [seq.id for seq in self.seqs]
#         # will not save bins or prototype. both can be created in deserialization
#         return D


#     def deserialize(self, D, deserialized_lower_layer=None):
#         super(Cluster, self).deserialize(D["super"])
#         if D["seqs"] is not None and deserialized_lower_layer is not None:
#             seqs = []
#             for seq_id in D["seqs"]:
#                 s = deserialized_lower_layer.hypotheses.reps[seq_id]
#                 seqs.append(s)
#             self.seqs = seqs
#         else:
#             print("Cluster::deserialize: Fatal error, deserialized_lower_layer information missing!")
#         return self


#     def find_prototype(self):
#         """ Use k-medoid approach for selecting the median sequence as prototype.
#         """

#         self.similarity_matrix, self.avg_sim, self.var_sim = within_cluster_similarity_statistics(self)

#         if self.prototype is None:
#             # 1a) if new cluster, select sequence as prototype
#             self.prototype = self.seqs[-1]
#         else:
#             # 1b) if cluster is updating
#             lenseq = len(self.seqs)
#             # 2) find sequence with minimal summed free energy
#             sum_sim = [np_sum(self.similarity_matrix[i, :, 2]) for i in range(lenseq)]
#             min_idx = np_argmax(sum_sim)

#             # 3) select that sequence as new prototype
#             self.prototype = self.seqs[min_idx]


#     def seqs_as_list(self):
#         return [s.as_array() for s in self.seqs]




# class Sequence(Representation):
#     """ Sequence specification of the representation class.
#     """

#     def __init__(self, idx="prototype"):
#         super(Sequence, self).__init__(idx)

#         self.seq = np.array([])
#         self.delta_t_seq = None  # delta_t of each seq[i+1]-seq[i]
#         self.discretized = None
#         self.alphabet = None


#     def __repr__(self):
#         return "ID:" + str(self.id) + " seq_ids: " + str(len(self.seq))  # + " delta_ts: " + str(self.delta_t_seq)


#     def serialize(self):
#         D = {}
#         D["super"] = super(Sequence, self).serialize()
#         if self.seq is not None:
#             seq = self.seq.tolist() if type(self.seq) is not list else self.seq
#             D["seq"] = [c.serialize() if type(c) is Coord else c for c in seq]
#         else:
#             D["seq"] = None
#         D["delta_t_seq"] = self.delta_t_seq if self.delta_t_seq is not None else None

#         return D


#     def deserialize(self, D, deserialized_lower_layer=None):
#         super(Sequence, self).deserialize(D["super"])

#         if D["seq"] is not None:
#             seq = []
#             for c in D["seq"]:
#                 coord = Coord()
#                 seq.append(coord.deserialize(c))
#             self.seq = np.array(seq)
#         self.delta_t_seq = D["delta_t_seq"] if D["delta_t_seq"] is not None else None

#         return self


#     def as_array(self):
#         return np.array([[float(polar.theta), float(polar.r), float(polar.drawing)] for polar in self.seq])




class Hypotheses(object):

    id_counter = 0

    def __init__(self):
        self.reps = {}
        self.dpd = np.empty((0, 0))  # will be set to be np.array later


    def __repr__(self):
        repr_str = ""
        for rep in self.reps.values():
            repr_str += str(rep.id) + " (" + str(rep) + ");\n"
        return repr_str


    def __len__(self):
        return len(self.reps)


    def serialize(self):
        D = {}
        if len(self.reps) > 0:
            D["rep_types"] = list(self.reps.values())[0].__class__.__name__
            D["reps"] = {key: rep.serialize() for key, rep in self.reps.items()}
            D["dpd"] = self.dpd.tolist()
            D["id_counter"] = self.id_counter
        return D


    def deserialize(self, D, deserialized_lower_layer=None):
        if "rep_types" in D:
            rep_type = D["rep_types"]
            reps = {}
            for key, rep in D["reps"].items():
                try:
                    key = float(key)
                except:
                    key = int(key)
                obj = None
                if rep_type == "Coord":
                    self.id_counter = D["id_counter"]
                    obj = Coord()
                if rep_type == "Representation":
                    self.id_counter = D["id_counter"]
                    obj = Representation(key)
                if rep_type == "Cluster":
                    self.id_counter = D["id_counter"]  # = int(float(np.max(list(D["reps"].keys()))))
                    obj = Cluster(key)
                if rep_type == "Sequence":
                    self.id_counter = D["id_counter"]  # = int(float(np.max(list(D["reps"].keys()))))
                    obj = Sequence(key)
                reps[key] = obj.deserialize(rep, deserialized_lower_layer)
            self.reps = reps
            self.dpd = np.array(D["dpd"])

            self.equalize()
            self.update_idx_id_mapping()
        return self


    def add_hypothesis(self, representation, P):
        """ Add a hypothesis and its starting probability.
        Also, create links from id to dpd_idx.
        """
        self.id_counter += 1
        self.reps[self.id_counter] = representation(self.id_counter)
        if len(self.dpd) == 0:
            self.dpd = np.array([[P, self.id_counter]])
        else:
            self.dpd = np.append(self.dpd, [[P, self.id_counter]], axis=0)
            # self.norm_dist()

        self.dpd = self.dpd[self.dpd[:, 1].argsort()]
        # make the index to ID pairing bidirectional
        for idx, dpd_pair in enumerate(self.dpd):
            self.reps[dpd_pair[1]].dpd_idx = idx
        # self.reps[self.id_counter].dpd_idx = len(self.dpd) - 1

        return self.reps[self.id_counter]


    def add_hypothesis_from_existing_repr(self, existing_repr, P):
        """ Add a hypothesis and its starting probability from an existing representation.
        """
        repr_id = existing_repr.id
        self.reps[repr_id] = existing_repr
        if len(self.dpd) == 0:
            self.dpd = np.array([[P, repr_id]])
        else:
            self.dpd = np.append(self.dpd, [[P, repr_id]], axis=0)

        self.dpd = self.dpd[self.dpd[:, 1].argsort()]
        # make the index to ID pairing bidirectional
        for idx, dpd_pair in enumerate(self.dpd):
            self.reps[dpd_pair[1]].dpd_idx = idx

        return self.reps[repr_id]


    def from_hypotheses(self, hypos):
        """ From a dictionary of hypothesis IDs and their representations create a
        discrete probability distribution which is equally distributed.
        """
        self.reps = hypos
        self.dpd = np.zeros((len(hypos), 2))
        one_by_len = 1. / len(hypos)
        self.dpd[:, :] = [[one_by_len, idx] for idx in sorted(hypos.keys())]
        # make the index to ID pairing bidirectional
        for idx, dpd_pair in enumerate(self.dpd):
            hypos[dpd_pair[1]].dpd_idx = idx


    def update_idx_id_mapping(self):
        """ Update the mapping from DPD id to Representation dpd_idx.
        """
        if self.dpd is not None and self.dpd.shape[0] > 0:
            # sort by id link ascending
            self.dpd = self.dpd[self.dpd[:, 1].argsort()]

            # update dpd_idx to make the index to ID pairing bidirectional again
            for idx, dpd_pair in enumerate(self.dpd):
                self.reps[dpd_pair[1]].dpd_idx = idx


    def diff_dists(self, other):
        """ Calculate the difference between discrete probability distributions.
        Assume the distributions are equally sorted.
        """
        # check for size difference
        if self.dpd.shape[0] == other.shape[0]:
            diff = self.dpd[:, 0] - other[:, 0]
            return np_sqrt(np_dot(diff, diff))
        else:
            # defenitely different!
            # print("diff_dists: Could not calculate distribution difference as distributions are not equally long!")
            return 1.0


    def norm_dist(self):
        """ Normalize the DPD.
        """
        # norm_factor = 1. / np.sum(self.dpd[:, 0])
        # self.dpd[:, 0] *= norm_factor
        add_one_smoothing = 1. / self.dpd.shape[0]
        norm_factor = 1. / np.sum(self.dpd[:, 0] + add_one_smoothing)
        self.dpd[:, 0] = (self.dpd[:, 0] + add_one_smoothing) * norm_factor


    def soft_max(self):
        """ Apply soft_max to hypothesis probability distribution
        """
        self.dpd[:, 0] = np.e**self.dpd[:, 0] / np.sum(np.e**self.dpd[:, 0], axis=0)


    def set_hypothesis_P(self, id, P):
        """ Introduce a specific probability of one of the representations.
        Normalize the distribution afterwards.
        """
        idx = self.reps[id].dpd_idx
        self.dpd[idx, 0] = P
        self.soft_max()


    def max(self):
        """ argmax to get the of max hypothesis tuple."""
        return self.dpd[np.argmax(self.dpd[:, 0])]


    def equalize(self):
        """ Equalize the probability distribution.
        """
        if self.dpd.shape[0] > 0:
            one_by_len = 1. / self.dpd.shape[0]
            self.dpd[:, 0] = one_by_len

        # self.erase_memory()



    def join(self, evidence):
        # sort by id link ascending
        self.dpd = self.dpd[self.dpd[:, 1].argsort()]
        evidence = evidence[evidence[:, 1].argsort()]
        # print("prior:", self.dpd[:, 1])
        # print("lh:", evidence[:, 1])

        # calculate posterior
        self.dpd = posterior(self.dpd, evidence)
        # update idx to id links
        self.update_idx_id_mapping()



