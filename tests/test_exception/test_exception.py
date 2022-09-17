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
            # remove class definition from registry
            registry._lineage.pop(NodeUnmatchedLayer)
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
        class NodeDuplicateName(NodeSI):
            def __str__(self):
                return 'node1'
        try:
            NodeDuplicateName()
        except:
            registry._lineage.pop(NodeDuplicateName)
        else:
            raise "Failed to catch a duplicated name"

    def test_nodesi_hookparent(self):
        @hook_parent([Node1, Node1])
        class NodeSI1(NodeSI):
            def __str__(self):
                return 'nodesi1'
        NodeSI1()

        @hook_parent(Node1, Node1)
        class NodeSI2(NodeSI):
            def __str__(self):
                return 'nodesi2'

        try:
            NodeSI1()
        except:
            # remove class definition from registry
            registry._lineage.pop(NodeSI1)
            registry._lineage.pop(NodeSI2)
        else:
            raise "Failed to check NodeSI"

    def test_seek_retr_check(self):
        root = Node1()
        node1c = root.seek('node1c')
        assert node1c and node1c.retr('node12')

        root.retr()
        assert root.retr('node1')

        try:
            root.seek('unexisted-node')
        except:
            pass
        else:
            raise "Failed to execute checking when seeking to node"

        try:
            root.retr('unexisted-node')
        except:
            pass
        else:
            raise "Failed to execute checking when retrospecting to node"