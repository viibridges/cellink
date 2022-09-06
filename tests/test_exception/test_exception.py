from graph import *

class Test:
    def test_unreachable_nodes(self):
        class Node4(NodeSI):
            def __str__(self):
                return 'node4'

            def forward(self):
                return True

        @hook_parent(Node4)
        class Node5(NodeSI):
            def __str__(self):
                return 'node5'

            def forward(self):
                return True

        root = Node1()
        try:
            root.seek('node5')
        except:
            pass
        else:
            raise "Failed to remove unreachable nodes from graph"

        root = Node4()
        assert root.seek('node5')


    def test_illegal_hook(self):
        @hook_parent(Node12, Node1C, [Node1, Node2, Node1])
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
