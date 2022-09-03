import sys
sys.path.append('.')

from lib.node import *
from lib.registry import hook_parent
from lib.registry import static_initializer

import numpy as np

class Node1(NodeSI):
    def __str__(self):
        return 'node1'

class Node2(NodeSI):
    def __str__(self):
        return 'node2'

    def forward(self):
        return True

@hook_parent([Node1, Node2])
class Node12(NodeSI):
    def __str__(self):
        return 'node12'

    @static_initializer
    def initialize_random_mat(self):
        random_mat = np.random.rand(5,5)
        return random_mat

    def forward(self):
        self.mat = self.initialize_random_mat()
        return True


class Layer(object):
    @static_initializer
    def initializer_shared(self):
        random_mat = np.random.rand(5,5)
        return random_mat

    def initializer_unique(self):
        raise NotImplementedError()

    def forward(self):
        self.quantum_mat = self.parent.mat
        self.shared_mat = self.initializer_shared()
        self.rand_mat = self.initializer_unique()
        return True


@hook_parent((Node12, 0))
class Node1C(Layer, NodeSI):
    def __str__(self):
        return 'node1c'

    @static_initializer
    def initializer_unique(self):
        random_mat = np.random.rand(5,5)
        return random_mat

@hook_parent((Node12, 1))
class Node2C(Layer, NodeSI):
    def __str__(self):
        return 'node2c'

    @static_initializer
    def initializer_unique(self):
        random_mat = np.random.rand(5,5)
        return random_mat