from graph import Input
from graph import Sqrt

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

        assert not hasattr(root['int-res'], 'val')

        root.seek('bigger')
        assert hasattr(root['int-res'], 'val')

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

    def test_broadcast(self):
        root = Input.initialize(3)
        greet_message = 'hello world!'
        root.broadcasting['message'] = greet_message
        node = root.seek('bigger')
        assert node.broadcasting['message'] == greet_message

        curse_message = 'go to hell!'
        node.broadcast({'message': curse_message})
        assert root.broadcasting['message'] == curse_message

    def test_weakref(self):
        def _throw_node():
            root = Input()
            return root['bigger']

        def _travel_up(node):
            for parent in node._parents:
                _travel_up(parent)

        node = _throw_node()
        try:
            _travel_up(node)
        except:
            pass
        else:
            raise RuntimeError("There are might be circular reference in the graph")

        # root is still there, this could work
        root = Input()
        node = root['bigger']
        _travel_up(node)
