from graph import *

class Test:
    def test_setup(self):
        Node1()

    def test_illegal_hook(self):
        @hook_parent(Node12, Node1C)
        class NodeUnmatchedLayer(NodeSI):
            def __str__(self):
                return 'unmatched layers'
        try:
            NodeUnmatchedLayer()
        except:
            pass
        else:
            raise "Failed to catch an illegal hook with unmatched layers"

    def test_duplicate_class(self):
        try:
            @hook_parent(Node1)
            class Node3(NodeSI):
                def __str__(self):
                    return 'nodeX'
        except:
            pass
        else:
            raise "Failed to catch a duplicated class"

    def test_duplicate_name(self):
        @hook_parent(Node1)
        class Node(NodeSI):
            def __str__(self):
                return 'node1'
        try:
            Node()
        except:
            pass
        else:
            raise "Failed to catch a duplicated name"
    # def test_seek(self):
    #     root = Node1()
    #     root.draw_graph()
    #     assert not root.seek('node5')