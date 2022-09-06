from graph import *

class Test:
    # def test_setup(self):
    #     root = Node1()
    #     # root.draw_graph(curve_edges=True)
    #     assert root.seek('node1c').val == 3
    #     assert root.seek('node5').val == 42

    #     root = Node1()
    #     node = root.seek('node5')
    #     node.retr()
    #     assert root['node1'].val == 4
    #     assert root['node2'].val == 2

    def test_layer_broadcasting(self):
        @hook_parent(Node4, Node1C)
        class NodeLayerBroadcasting1(NodeMI):
            pass
        @hook_parent(Node1C, Node4)
        class NodeLayerBroadcasting2(NodeMI):
            pass
        @hook_parent(Node1C, Node4, [Node1C, Node1C])
        class NodeLayerBroadcasting3(NodeMI):
            pass

        Node1()
        # NodeLayerBroadcasting1()
        # NodeLayerBroadcasting2()
        # NodeLayerBroadcasting3()