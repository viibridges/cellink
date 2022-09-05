import sys
sys.path.append('.')

from lib.node import *
from lib.registry import hook_parent

class Node1(NodeSI):
    def __str__(self):
        return 'node1'

    def forward(self):
        self.val = 3
        return True

class Node2(NodeSI):
    def __str__(self):
        return 'node2'

    def forward(self):
        self.val = 1
        return True

@hook_parent(Node1, Node2)
class Node3(NodeMI):
    def __str__(self):
        return 'node3'

    def forward(self):
        self.val = self.parent_list[0].val + self.parent_list[1].val
        return True

@hook_parent([Node1, Node2])
class Node12(NodeSI):
    def __str__(self):
        return 'node12'

    def forward(self):
        self.offset = self.parent.val
        self.val = self.parent.val / 2
        return True

    def backward(self):
        self.parent.val = self.val + self.offset
        return True

@hook_parent((Node12, 0))
class Node1C(NodeSI):
    def __str__(self):
        return 'node1c'

    def forward(self):
        self.val = self.parent.val * 2
        return True

@hook_parent(Node3, (Node12, 0), (Node12, 1))
class Node4(NodeMI):
    def __str__(self):
        return 'node4'

    def forward(self):
        quantum_val = self.parent_list[1].val + self.parent_list[2].val
        self.val = self.parent_list[0].val/2 - quantum_val
        return True

    def backward(self):
        self.parent_list[1].val = self.val - 41
        self.parent_list[2].val = self.val - 41
        return True

@hook_parent(Node4)
class Node5(NodeSI):
    def __str__(self):
        return 'node5'

    def forward(self):
        self.val = self.parent.val + 42
        return True

    def backward(self):
        self.parent.val = self.val
        return True