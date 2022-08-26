from lib.node import *
from lib.registry import hook_parent
from lib.registry import static_initializer

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
        return 'numb'

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


@hook_parent(Square, Substract)
class Plus(NodeMI):
    def __str__(self):
        return 'plus'

    def forward(self):
        val1 = self.parent_list[0].val
        val2 = self.parent_list[1].val
        self.val = val1 + val2
        return True
