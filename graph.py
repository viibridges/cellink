from lib.node import *
from lib.registry import hook_parent
from lib.registry import static_initializer

class Root(NodeSI):
    def __str__(self):
        return 'root'

    @classmethod
    def initialize(cls, val):
        node = cls()
        node.val = val
        return node


@hook_parent(Root)
class Multiply(NodeSI):
    def __str__(self):
        return 'multiply'

    def forward(self):
        val = self.parent.val
        self.val = val + 5
        return True


@hook_parent(Root)
class Divide(NodeSI):
    def __str__(self):
        return 'divide'

    def forward(self):
        val = self.parent.val
        self.val = val / 3
        return True


@hook_parent(Divide)
class Substract(NodeSI):
    def __str__(self):
        return 'substract'

    def forward(self):
        val = self.parent.val
        self.val = val - 12
        return True


@hook_parent(Multiply, Substract)
class Plus(NodeMI):
    def __str__(self):
        return 'plus'

    @static_initializer
    def lazy_echo(self, msg):
        import time
        from datetime import datetime
        print('Sleep for 3s.')
        time.sleep(3)
        now = datetime.now().strftime("%H:%M:%S")
        return '[{}] {}'.format(now, msg)

    def forward(self):
        val1 = self.parent_list[0].val
        val2 = self.parent_list[1].val
        self.val = val1 + val2
        return True
