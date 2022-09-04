import sys
sys.path.append('.')

from lib.node import *
from lib.registry import hook_parent

class Node1(NodeSI):
    def __str__(self):
        return 'node1'

class Node2(NodeSI):
    def __str__(self):
        return 'node2'

    def forward(self):
        return True

@hook_parent(Node1, Node2)
class Node3(NodeMI):
    def __str__(self):
        return 'node3'

    def forward(self):
        return True

@hook_parent([Node1, Node2])
class Node12(NodeSI):
    def __str__(self):
        return 'node12'

    def forward(self):
        return True

@hook_parent((Node12, 0))
class Node1C(NodeSI):
    def __str__(self):
        return 'node1c'

    def forward(self):
        return True
