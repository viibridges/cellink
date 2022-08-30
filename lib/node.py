from .registry import registry
import weakref

class NodeBase(object):
    def __init__(self, bootstrap_node=True):
        """
        Initialize a node.

        Args:
            - bootstrap_node: whether current node is the bootstrap node (True by default).
            A graph is usually built from one node (by calling classmethod), which we call it
            bootstrap node.
            __init__() of the none-bootstrap nodes is called recursively in
            self._build_graph, where bootstrap_node should be disabled to avoid
            chain-reaction from happenning.
        """
        # node node object container, to keep track of the edges of the graph
        # each node saves only its parents and the children
        self._parents  = []
        self._children = []

        # dynamic states, to record if an node node being forwarded/backwarded
        # None: unvisited, True: forward succeeded, False: forward failed
        self._forward_state = None

        # internal nodes that hides beneath the representation node
        self._quantum_layers = []

        # start building the graph
        if bootstrap_node:
            self._build_graph(dict())
            self._check_graph()

            # notice board, on which messages are synchronized/updated across all nodes
            #  in the graph, when calling broadcast() method from any node
            notice_board = dict()
            def _setup_notice_board(node):
                # setup notice board to all nodes
                for node in [node] + node._quantum_layers:
                    node.__setattr__('_notice_board', notice_board)
            self._traverse_graph(_setup_notice_board)


    @property
    def isroot(self):
        return len(self._parents) == 0

    def __str__(self):
        return type(self).__name__

    def _initialize(self):
        raise NotImplementedError()

    def _get_layer(self, layer_id):
        if len(self._quantum_layers) == 0:
            assert layer_id == 0
            return self
        else:
            assert layer_id < len(self._quantum_layers)
            return self._quantum_layers[layer_id]

    def _get_layers(self):
        if len(self._quantum_layers) == 0:
            return [self]
        else:
            return self._quantum_layers

    def _build_graph(self, visited_nodes):
        """
        Build the whole graph of the node, where nodes are node instances,
        connected each others by variable _parents and _children.

        Args:
            - visited_nodes: dict of node instances that have been initialized during graph building
        """
        if type(self) in visited_nodes:
            return

        # break the reference circle, which may cause trouble for python
        # garbage collection mechanism, by replacing _parents elements with
        # weakref
        # NOTE: weakref objects aren't hashable
        visited_nodes[type(self)] = weakref.proxy(self)

        ## 1) register parent-subgraph
        for static_info in registry[type(self)].parents:
            parent_cls = static_info['class']
            if parent_cls not in visited_nodes:
                parent = parent_cls(bootstrap_node=False)
                parent._build_graph(visited_nodes)
                # print("{} builds parent {}".format(self, parent))
            else:
                parent = visited_nodes[parent_cls]
            self._parents.append(parent)

        ## 2) build internal layers
        static_parents = registry[type(self)].parents
        assert len(self._parents) == len(static_parents)

        # 2.1) get quantum space: {parentID: layer_list}
        quantum_space = dict()
        for parent_node, static_info in zip(self._parents, static_parents):
            parent_layer_id, parent_id = static_info['layer_id'], static_info['parent_id']
            if parent_id not in quantum_space:
                quantum_space[parent_id] = list()
            if parent_layer_id > 0:
                parent_layer = parent_node._get_layer(parent_layer_id)
                quantum_space[parent_id].append(parent_layer)
            else:
                for parent_layer in parent_node._get_layers():
                    quantum_space[parent_id].append(parent_layer)

        # 2.2) put contents from quantum space to self
        is_quantum_node = len(quantum_space) > 0 and len(quantum_space[0]) > 1
        if is_quantum_node:
            num_layers = len(quantum_space[0])
            for layer_id in range(num_layers):
                layer = type(self)(bootstrap_node=False)
                for parent_id in range(len(quantum_space)):
                    assert len(quantum_space[parent_id]) == num_layers
                    parent_layer = quantum_space[parent_id][layer_id]
                    layer._parents.append(parent_layer)
                    parent_layer._children.append(layer)
                self._quantum_layers.append(layer)
        else:
            pass
            # for parent_id in range(len(quantum_space)):
            #     assert len(quantum_space[parent_id]) == 1
            #     parent_layer = quantum_space[parent_id][0]
            #     self._parents.append(parent_layer)
            #     parent_layer._children.append(self)

        # 2.3) initialization
        if is_quantum_node:
            for layer in self._quantum_layers:
                layer._initialize()
        self._initialize()

        ## 3) register child-subgraph
        for static_info in registry[type(self)].children:
            child_cls = static_info['class']
            if child_cls not in visited_nodes:
                child = child_cls(bootstrap_node=False)
                child._build_graph(visited_nodes)
                # print("{} builds child {}".format(self, child))
            else:
                child = visited_nodes[child_cls]
            self._children.append(child)

    def _check_graph(self):
        """
        check the naming uniqueness of all nodes
        """
        node_names = self._traverse_graph(lambda node: str(node))
        unique_names = set(node_names)
        if len(unique_names) < len(node_names):
            raise RuntimeError("Duplicated names found in graph: {}".format(sorted(node_names)))

    def forward(self):
        # root doesn't need forward
        return self.isroot

    def backward(self):
        return False

    def _run_forward(self):
        if self._forward_state is None:
            success = self.forward()
            if success not in [True, False]:
                raise RuntimeError(
                    "{} forward() should return either 'True' or 'False', "
                    "while it returns: {}".format(type(self), success)
                )
            else:
                self._forward_state = success
        return self._forward_state

    def _run_backward(self):
        success = self.backward()
        if success not in [True, False]:
            raise RuntimeError(
                "{} backward() should return either 'True' or 'False', "
                "while it returns: {}".format(type(self), success)
            )
        else:
            return success

    def seek(self, node_name:str):
        """
        reach node by executing series of forward() methods.
        NOTE: unlike method retr(), seek() can start from any node

        Args:
            node_name: a string, name of the node to return

        Return:
            the node object with the node_name
        """
        def _forward_to_node(node):
            if node._forward_state:
                return True
            if isinstance(node, NodeCI):
                # if current node is NodeCI, keep forwarding as lone as it has >= one parent alive
                parent_states = [_forward_to_node(parent) for parent in node._parents]
                if not any(parent_states):
                    return False
                else:
                    # update the public variable 'parent_list' of NodeCI
                    assert hasattr(node, 'parent_list')
                    new_parent_list = list()
                    for parent, alive in zip(node.parent_list, parent_states):
                        new_parent_list.append(parent if alive else None)
                    node.parent_list = new_parent_list
            else:
                for parent in node._parents:
                    if not _forward_to_node(parent):  # immediate stop if one dead parent found
                        return False
            return node._run_forward()

        target_node = self[node_name]
        success = _forward_to_node(target_node)
        return target_node if success else None

    def retr(self, node_name:str=None):
        """
        reach node in a bottom-up manner by executing series of backward() methods

        Args:
            node_name: a string, name of the node to return

        Return:
            the node object with the node_name
        """
        # find the node
        if str(self) == node_name:
            return self

        # keep scanning upwards
        elif self._run_backward():
            for parent in self._parents:
                parent.retr(node_name)
        else:
            return None

        if node_name is None:
            return None
        else:
            return self[node_name]

    def _traverse_graph(self, callback):
        """
        traverse the graph and execute call_back at each node (with random order)

        Args:
            callback: a callback function that receive a node as input

        Return:
            a dictionary of returning results: {str(node): callback(node) return}
        """
        ## 1) Collect all node instances
        all_nodes_in_graph = dict() # dict that stores all nodes in graph
        queue = [self]
        while len(queue) > 0:
            node = queue.pop()
            all_nodes_in_graph.update({str(node):node})
            # insert unvisited nodes to queue (can't use set to compute differences
            # because some nodes are weakref objects, which aren't hashable)
            neighbors = {str(n):n for n in node._children+node._parents}
            for name, n in neighbors.items():
                if name not in all_nodes_in_graph:
                    queue.append(n)

        ## 2) Execute results
        assert callable(callback), "The input must be a callable funciton."
        return [callback(node) for node in all_nodes_in_graph.values()]

    def __getitem__(self, node_name:str):
        # get representatives of all nodes: their first layer
        all_nodes = self._traverse_graph(lambda node: node)
        for node in all_nodes:
            if str(node) == node_name:
                return node
        raise RuntimeError("Can not find node named '{}' in graph".format(node_name))

    def broadcast(self, message):
        """
        Broad cast message to all nodes (update message to their _notice_board)
        """
        assert isinstance(message, dict), "message needs to be a dictionary"
        self._notice_board.update(message)

    def traverse(self, callback):
        """
        run callback() in all node nodes of the graph
        """
        return self._traverse_graph(callback)

    @property
    def broadcasting(self):
        return self._notice_board


    #
    # Graph drawing related
    #
    @staticmethod
    def _get_node_attribute(node):
        if node.isroot:
            return {'color': 'red', 'style': 'filled'}
        elif len(node._quantum_layers) > 0: # quantum node
            return {'color': '.7 .3 1.', 'style': 'filled', 'fontcolor': 'white'}
        elif isinstance(node, NodeCI):
            return {'color': 'blue', 'style': 'filled', 'fontcolor': 'white'}
        else:
            return {}

    def draw_graph(self, node_name=None, curve_edges=False):
        from graphviz import Digraph
        g = Digraph('G', filename='graph')
        g.attr('node', shape='box')
        g.graph_attr['splines'] = 'true' if curve_edges else 'false'

        if not node_name:
            self._draw_whole_graph(g)
        else:
            node = self[node_name]
            self._draw_parent_graph(g, node, set())

        g.render(view=False, cleanup=True)

    def _draw_whole_graph(self, g):
        all_nodes = self._traverse_graph(lambda node: node)
        for node in all_nodes:
            for parent in node._parents:
                g.edge(str(parent), str(node))
            g.node(str(node), **self._get_node_attribute(node))

    def _draw_parent_graph(self, g, node, visited_edges):
        for parent in node._parents:
            edge_name = str(parent)+'/'+str(node)
            if edge_name not in visited_edges:
                visited_edges.add(edge_name)
                g.edge(str(parent), str(node))
                g.node(str(node), **self._get_node_attribute(node))
                g.node(str(parent), **self._get_node_attribute(parent))
                self._draw_parent_graph(g, parent, visited_edges)


class NodeSI(NodeBase):
    def _initialize(self):
        if len(self._quantum_layers) > 0:
            assert all([len(layer._parents) == 1 for layer in self._quantum_layers])
        else:
            assert len(self._parents) in [0, 1]  # 0 for root node case
        self.parent = None if len(self._parents) == 0 else self._parents[0]

class NodeMI(NodeBase):
    def _initialize(self):
        self.parent_list = self._parents

class NodeCI(NodeBase):
    def _initialize(self):
        self.parent_list = self._parents
