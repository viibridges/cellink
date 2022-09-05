from graph import *

class Test:
    def test_setup(self):
        root = Node1()
        # root.draw_graph(curve_edges=True)
        assert root.seek('node1c').val == 3
        assert root.seek('node5').val == 42

        root = Node1()
        node = root.seek('node5')
        node.retr()
        assert root['node1'].val == 4
        assert root['node2'].val == 2