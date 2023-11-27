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
        root.draw_graph()

    def test_indexing(self):
        root = Input.initialize(3)
        node_indexed = root['sqrt']
        node_seeked = root.seek('sqrt')
        assert node_indexed == node_seeked

        node = root[node_indexed]
        assert node == node_indexed

        node = root.seek(node_seeked)
        assert node == node_seeked

        all_nodes = root._traverse_graph(lambda node: node, mode='complete')
        for node in all_nodes:
            if str(node) == 'sqrt' and node._quantum_id == 1:
                break
        assert not hasattr(node, 'val')
        node_quantum = root.seek(node)
        assert hasattr(node, 'val')
        assert node_quantum == node


    def test_seek(self):
        root = Input.initialize(3)
        node = root.seek('plus')
        assert node.val == 214

        node = root.seek('float-res')
        assert node.val == 1

        assert not hasattr(root['int-res'], 'val')

        # seek to input node
        node = root.seek('input')
        assert node.val == 3
        node = root.seek('factor')
        assert node.val == 5

        # test condition node
        node = root.seek('bigger')
        assert hasattr(root['int-res'], 'val')
        assert node.parent_list[0] is not None
        assert node.parent_list[1] is None
        assert node.val == 214

        # single input condition
        node = root.seek('float-cond')
        assert node.val == 1

        # dead condition
        assert not root.seek('dead-cond')

        # test not node
        node = root.seek('not-s>p')
        assert node
        node.val == 3.14

        assert not root.seek('not-dead-cond')

    def test_retr(self):
        root = Input.initialize(3)
        node = root.seek('bigger')
        assert not node.retr()
        assert root.val == -123
        node_mul = node.retr('multiply')
        assert node_mul.val == -123
        assert str(node_mul) == 'multiply'
        node_int = node.retr('integer')
        assert not node_int

        root = Input.initialize(3)
        node = root.seek('plus')
        node_bigger = node.retr('bigger')
        assert not node_bigger

        # retr from root dir
        root.retr()

        # retr to root
        node = root.seek('plus')
        assert node.retr('input')

    def test_condition_node(self):
        root = Input.initialize(3)
        node1 = root.seek('int-res')
        node2 = root.seek('plus')
        node3 = root.seek('bigger')

        if node1.val > node2.val:
            assert node1.val == node3.val
        else:
            assert node2.val == node3.val

    def test_parallel_node(self):
        root = Input.initialize(3)
        node1 = root.seek('+1')
        node2 = root.seek('+3')
        node3 = root.seek('x3')
        node_bad = root.seek('broken')

        assert not node_bad
        assert node1.val == 65
        assert node2.val == 67
        assert node3.val == 192

        # TODO: support backward in the future
        # node_int = node3.retr('integer')
        # assert node_int.val == 192

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
