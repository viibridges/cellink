import sys
sys.path.append('.')

from lib.node import *
from lib.registry import hook_parent
import numpy as np

class Input(NodeSI):
    def __str__(self):
        return 'input'

    @classmethod
    def initialize(cls, val):
        node = cls()
        node.val = val
        return node


class Factor(NodeSI):
    def __str__(self):
        return 'factor'

    def forward(self):
        self.val = 5
        return True


@hook_parent(Input, Factor)
class Multiply(NodeMI):
    def __str__(self):
        return 'multiply'

    def forward(self):
        val = self.parent_list[0].val
        factor = self.parent_list[1].val
        self.val = val * factor
        return True

    def backward(self):
        self.parent_list[0].val = self.val
        return True


class Denominator(NodeSI):
    def __str__(self):
        return 'denominator'

    def forward(self):
        self.val = 3
        return True


@hook_parent(Input, Denominator)
class Divide(NodeMI):
    def __str__(self):
        return 'divide'

    def forward(self):
        nominator = self.parent_list[0].val
        denominator = self.parent_list[1].val
        self.val = nominator / denominator
        return True


class Number(NodeSI):
    def __str__(self):
        return 'number'

    def forward(self):
        self.val = 12
        return True


@hook_parent(Divide, Number)
class Substract(NodeMI):
    def __str__(self):
        return 'substract'

    def forward(self):
        val = self.parent_list[0].val
        num = self.parent_list[1].val
        self.val = val - num
        return True


@hook_parent(Multiply)
class Square(NodeSI):
    def __str__(self):
        return 'square'

    def forward(self):
        val = self.parent.val
        self.val = val * val
        return True

    def backward(self):
        self.parent.val = self.val
        return True


@hook_parent(Square, Substract)
class Plus(NodeMI):
    def __str__(self):
        return 'plus'

    def forward(self):
        val1 = self.parent_list[0].val
        val2 = self.parent_list[1].val
        self.val = val1 + val2
        return True

    def backward(self):
        self.parent_list[0].val = self.val
        return True


class Integer(NodeSI):
    def __str__(self):
        return 'integer'

    def forward(self):
        self.val = 64
        return True


class Float(NodeSI):
    def __str__(self):
        return 'float'

    def forward(self):
        self.val = 100.0
        return True


@hook_parent([Integer, Plus, Float])
class Sqrt(NodeSI):
    def __str__(self):
        return 'sqrt'

    def forward(self):
        val = self.parent.val
        self.val = np.sqrt(val)
        return True

    def backward(self):
        self.parent.val = self.val
        return True


@hook_parent(Sqrt)
class Log(NodeSI):
    def __str__(self):
        return 'log'

    def forward(self):
        val = self.parent.val
        self.val = np.log(val) / np.log(10)
        return True


@hook_parent((Log, 2))
class FloatRes(NodeSI):
    def __str__(self):
        return 'float-res'

    def forward(self):
        self.val = self.parent.val
        return True


@hook_parent((Sqrt, 1))
class IntRes(NodeSI):
    def __str__(self):
        return 'int-res'

    def forward(self):
        self.val = self.parent.val
        return True


@hook_parent(Plus, IntRes)
class Cond1(NodeMI):
    def __str__(self):
        return 'p>s'

    def forward(self):
        val1 = self.parent_list[0].val
        val2 = self.parent_list[1].val
        if val1 > val2:
            self.val = val1
            return True
        else:
            return False

    def backward(self):
        self.parent_list[0].val = self.val
        return True


@hook_parent(Plus, IntRes)
class Cond2(NodeMI):
    def __str__(self):
        return 's>p'

    def forward(self):
        val1 = self.parent_list[0].val
        val2 = self.parent_list[1].val
        if val1 < val2:
            self.val = val2
            return True
        else:
            return False


@hook_parent(Cond1, Cond2)
class Cond(NodeCI):
    def __str__(self):
        return 'bigger'

    def forward(self):
        p1 = self.parent_list[0]
        p2 = self.parent_list[1]

        if not p1:
            assert p2 is not None
            self.val = p2.val
        else:
            assert p1 is not None
            self.val = p1.val
        return True

    def backward(self):
        self.parent_list[0].val = -123
        return True


@hook_parent(FloatRes)
class CondFloat(NodeCI):
    def __str__(self):
        return 'float-cond'

    def forward(self):
        self.val = self.parent_list[0].val
        return True


@hook_parent(Cond2)
class DeadCond(NodeCI):
    def __str__(self):
        return 'dead-cond'

    def forward(self):
        self.val = self.parent_list[0].val
        return True


@hook_parent(DeadCond)
class NotDeadCond(NodeNI):
    def __str__(self):
        return 'not-dead-cond'

    def forward(self):
        self.val = 3.14
        return True


@hook_parent(Cond2)
class NotCond2(NodeNI):
    def __str__(self):
        return 'not-s>p'

    def forward(self):
        self.val = 3.14
        return True


@hook_parent(Integer)
class Plus1(NodePI):
    def __str__(self):
        return '+1'

    def forward(self):
        self.val = self.parent.val + 1
        return True


@hook_parent(Integer)
class Broken(NodePI):
    def __str__(self):
        return 'broken'

    def forward(self):
        self.val = self.parent.val
        return False


@hook_parent(Integer)
class Plus3(NodePI):
    def __str__(self):
        return '+3'

    def forward(self):
        self.val = self.parent.val + 3
        return True


@hook_parent(Integer)
class Mul3(NodePI):
    def __str__(self):
        return 'x3'

    def forward(self):
        self.val = self.parent.val * 3
        return True

    def backward(self):
        self.parent.val = self.val
        return True
    

@hook_parent(Broken)
class Plus2(NodeNI):
    def __str__(self):
        return '+2'

    def forward(self):
        self.val = self.parent.val + 2
        return True