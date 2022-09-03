from graph_common import Input
from graph_common import Sqrt

class Test:
    def test_setup(self):
        root1 = Input()
        root2 = Sqrt()
        root1['sqrt']
        root2['input']

    def test_draw_graph(self):
        root = Input()
        root.draw_graph()
        root = Sqrt()
        root.draw_graph(curve_edges=True)

    def test_seek(self):
        root = Input.initialize(3)
        node = root.seek('plus')
        assert node.val == 214

        node = root.seek('float-res')
        assert node.val == 1

    def test_condition_node(self):
        root = Input.initialize(3)
        node1 = root.seek('int-res')
        node2 = root.seek('plus')
        node3 = root.seek('bigger')

        if node1.val > node2.val:
            assert node1.val == node3.val
        else:
            assert node2.val == node3.val

    def test_backward(self):
        root = Input.initialize(3)
        node = root.seek('bigger')
        node.retr()
        assert root.val == -123

