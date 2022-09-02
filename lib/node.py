from .registry import registry
import weakref

class NodeInfo(object):
    def __init__(self, layer_id = 0, total_layers = 1):
        self.parents = []                 # parent nodes of current NODE
        self.layer_id = layer_id          # layer index
        self.total_layers = total_layers  # number of total layer

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
        # dynamic states, to record if an node node being forwarded/backwarded
        # None: unvisited, True: forward succeeded, False: forward failed
        self._forward_state = None

        # start building the graph
        if bootstrap_node:
            self._build_graph()
            self._check_graph()

            # notice board, on which messages are synchronized/updated across all nodes
            #  in the graph, when calling broadcast() method from any node
            notice_board = dict()
            set_notice_board = lambda node: setattr(node, '_notice_board', weakref.proxy(notice_board))
            self._traverse_graph(set_notice_board, mode='complete')
            self._notice_board = notice_board

    @property
    def _parents(self):
        return self._graph[self].parents

    @property
    def _num_layers(self):
        return self._graph[self].total_layers

    @property
    def isroot(self):
        return len(self._parents) == 0

    def __str__(self):
        return type(self).__name__

    def _get_class2nodes(self):
        class2nodes = dict()
        for node, node_info in self._graph.items():
            layer_id = node_info.layer_id
            if type(node) not in class2nodes:
                class2nodes[type(node)] = dict()
            assert layer_id not in class2nodes[type(node)]
            class2nodes[type(node)][layer_id] = node
        return class2nodes

    def _build_graph(self):
        """
        Build the whole graph by creating node instances and put them under the
        management of _graph
        """
        ## 0) initialize the graph
        self._graph = {self: NodeInfo()}

        ## 1) create all nodes in graph (excluding self)
        def _create_nodes(NodeClass):
            ## 0) handle root nodes
            if len(registry[NodeClass]) == 0: # NodeClass is a root node class
                node = NodeClass(bootstrap_node=False)
                self._graph[node] = NodeInfo()
                # node._graph = weakref.proxy(self._graph)
                node._graph = self._graph
                return None

            ## 1) preparation
            # initialize nodes for all layers: node_info_pair
            layer_id = 0
            node_info_pair = dict()  # (node instance, empty NodeInfo instance, parent_layer_id)
            # registry[NodeClass] has format as: [[(NodeClass, layer_id),(...)], [(...)]]
            for parent_class, parent_layer_id in registry[NodeClass][0]:
                if parent_layer_id > 0:
                    node = NodeClass(bootstrap_node=False)
                    node_info_pair[layer_id] = \
                        (node, NodeInfo(layer_id=layer_id), parent_layer_id)
                    layer_id += 1
                else:
                    class2nodes = self._get_class2nodes()
                    if parent_class not in class2nodes:
                        _create_nodes(parent_class)
                        class2nodes = self._get_class2nodes()
                    num_parent_layers = len(class2nodes[parent_class])
                    for parent_layer_id in range(num_parent_layers):
                        node = NodeClass(bootstrap_node=False)
                        node_info_pair[layer_id] = \
                            (node, NodeInfo(layer_id=layer_id), parent_layer_id)
                        layer_id += 1

            

            ## 2) add parents to the right place in node_info (node_info_pair)
            class2nodes = self._get_class2nodes()
            # registry[NodeClass] has format as: [[(NodeClass, layer_id),(...)], [(...)]]
            for parent_class_list in registry[NodeClass]:
                # parent_class_list has format as: [(NodeClass, layer_id),(...)]
                for parent_class, _ in parent_class_list:
                    assert parent_class in class2nodes
                    # parent_node_dict has format as: {parent_layer_id: parent node instance}
                    parent_node_dict = class2nodes[parent_class]
                    for layer_id in range(len(node_info_pair)):
                        node, node_info, parent_layer_id = node_info_pair[layer_id]
                        assert parent_layer_id in parent_node_dict
                        parent_node = parent_node_dict[parent_layer_id]
                        node_info.parents.append(parent_node)

            # register node_info_pair to _graph
            for node, node_info, _ in node_info_pair.values():
                node_info.total_layers = len(node_info_pair) # update total_layers
                self._graph[node] = node_info
                # node._graph = weakref.proxy(self._graph)
                node._graph = self._graph

        for NodeClass in registry._lineage:
            if not isinstance(self, NodeClass):
                _create_nodes(NodeClass)


    def _check_graph(self):
        """
        check the naming uniqueness of all nodes
        """
        node_names = self._traverse_graph(lambda node: str(node), mode='surface')
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

    def _traverse_graph(self, callback, mode: str):
        """
        traverse the graph and execute call_back at each node (with random order)

        Args:
            -callback: a callback function that receive a node as input
            -mode: in ['surface', 'complete']; complete mode process nodes of all
            levels, while surface mode only scratch the first layer

        Return:
            a dictionary of returning results: {str(node): callback(node) return}
        """
        assert mode in ['surface', 'complete']
        node_set = set()
        ## 1) Collect all node instances
        for node_dict in self._get_class2nodes().values():
            if mode == 'surface':
                node_set.add(node_dict[0])
            else:
                node_set.union(node_dict.values())

        ## 2) Execute results
        assert callable(callback), "The input must be a callable funciton."
        return [callback(node) for node in node_set]

    def __getitem__(self, node_name:str):
        # get representatives of all nodes: their first layer
        all_nodes = self._traverse_graph(lambda node: node, mode='surface')
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
        return self._traverse_graph(callback, mode='surface')

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
        elif node._num_layers > 1: # quantum node
            return {'color': '.7 .3 1.', 'style': 'filled', 'fontcolor': 'white'}
        elif isinstance(node, NodeCI):
            return {'color': 'blue', 'style': 'filled', 'fontcolor': 'white'}
        else:
            return {}

    def draw_graph(self, curve_edges=False):
        from graphviz import Digraph
        g = Digraph('G', filename='graph')
        g.attr('node', shape='box')
        g.graph_attr['splines'] = 'true' if curve_edges else 'false'

        all_nodes = self._traverse_graph(lambda node: node, mode='surface')
        for node in all_nodes:
            for parent in node._parents:
                g.edge(str(parent), str(node))
            g.node(str(node), **self._get_node_attribute(node))

        g.render(view=False, cleanup=True)


class NodeSI(NodeBase):
    """
    Definition of nodes that have only one parent
    """
    @property
    def parent(self):
        return self._parents[0]

class NodeMI(NodeBase):
    """
    Definition of nodes that have more than one parents;
    Seekable when all its parents are seekable
    """
    @property
    def parent_list(self):
        return self._parents

class NodeCI(NodeBase):
    """
    Definition of nodes that have more than one parents;
    Seekable if any one of its parents is seekable
    """
    @property
    def parent_list(self):
        return self._parents
