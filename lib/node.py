from .registry import registry
from .graph import Graph
import weakref
import copy
import uuid
import hashlib

class NodeBase(object):
    def __init__(self, bootstrap_node=True):
        """
        Initialize a node.

        Args:
            - bootstrap_node: whether current node is the bootstrap node (True by default).
            A graph is usually built from one node (by calling classmethod), which we call it
            bootstrap node.
        """
        # create identity, which won't change when being weakly referenced
        self._identity = hashlib.md5(uuid.uuid1().bytes).hexdigest()

        # dynamic states, to record if an node node being forwarded/backwarded
        # None: unvisited, True: forward succeeded, False: forward failed
        self._forward_state = None

        # start building the graph
        if bootstrap_node:
            self._build_graph()
            self._check_graph()

    @property
    def _parents(self):
        return self._graph[self]['parents']

    @property
    def _is_root(self):
        return self._graph[self]['root']

    @property
    def _is_quantum(self):
        return self._graph[self]['quantum']

    def __str__(self):
        return type(self).__name__

    def __eq__(self, obj):
        return self._identity == obj._identity

    def _initialize_node(self):
        pass

    def _check_graph(self):
        """
        check the naming uniqueness of all nodes
        """
        node_names = self._traverse_graph(lambda node: str(node), mode='surface')
        unique_names = set(node_names)
        if len(unique_names) < len(node_names):
            raise RuntimeError("Duplicated names found in graph: {}".format(sorted(node_names)))

    def _get_clean_lineage(self):
        """
        Get clean lineage from registry:
        Remove unreachable class definition from graph
        """
        static_lineage = copy.copy(registry._lineage)

        ## 1) add children to node
        children_dict = dict() # {node_class: [child node class, ...]}
        parent_dict   = dict()
        for node_class, formated_parent_list in static_lineage.items():
            # collect parent class list
            parent_class_list = []
            for parent_group in formated_parent_list:
                for parent_class, _ in parent_group:
                    parent_class_list.append(parent_class)
            # update children_dict
            children_dict[node_class] = parent_class_list
            # update class2children
            for parent_class in parent_class_list:
                if parent_class not in parent_dict:
                    parent_dict[parent_class] = []
                parent_dict[parent_class].append(node_class)

        ## 2) traverse graph from self (bootstrap node)
        unreached_classes = set(static_lineage.keys())
        queue = [type(self)]
        while len(queue) > 0:
            node_class = queue.pop()
            if node_class in unreached_classes:
                unreached_classes.remove(node_class)
            children = children_dict.get(node_class, [])
            parents  = parent_dict.get(node_class, [])
            for neighbor in children+parents:
                if neighbor in unreached_classes:
                    queue.append(neighbor)

        ## 3) remove unreached nodes from graph
        for node_class in unreached_classes:
            static_lineage.pop(node_class)

        ## 4) expand the registry lineage
        nlayers_table = dict()
        def _get_node_layers(node_class):
            parent_list = static_lineage[node_class]
            if node_class in nlayers_table:
                return nlayers_table[node_class]
            elif len(parent_list) == 0: # root node has one layer
                return 1
            else:
                num_layers = 0
                for parent_class, parent_layer_id in parent_list[0]:
                    if parent_layer_id >= 0:
                        num_layers += 1
                    else:
                        num_layers += _get_node_layers(parent_class)
                nlayers_table[node_class] = num_layers
                return num_layers

        for node_class, parent_list in static_lineage.items():
            new_parent_list = list()
            for parent_group in parent_list:
                new_parent_group = list()
                for parent_class, parent_layer_id in parent_group:
                    if parent_layer_id >= 0:
                        new_parent_group.append((parent_class, parent_layer_id))
                    else:
                        num_layers = _get_node_layers(parent_class)
                        new_parent_group.extend([(parent_class, idx) for idx in range(num_layers)])
                new_parent_list.append(new_parent_group)
            static_lineage[node_class] = new_parent_list
            # check the number of parent layers to secure matches
            parent_layer_nums = set(len(grp) for grp in new_parent_list)
            assert len(parent_layer_nums) in [0, 1], "Parent layer number mismatches: {}".format(node_class)

        return static_lineage

    def _build_graph(self):
        """
        Build the whole graph by creating node instances and put them under the
        management of _graph
        """
        ## 1) collect graph infos
        static_lineage = self._get_clean_lineage()
        class2info = dict()
        for node_class, parent_list in static_lineage.items():
            class2info[node_class] = dict()
            num_layers = 1 if len(parent_list) == 0 else len(parent_list[0])
            class2info[node_class]['num_layers'] = num_layers
            class2info[node_class]['node_layers'] = [node_class(bootstrap_node=False) for _ in range(num_layers)]
            # replace the first layer if node_class is current node
            if isinstance(self, node_class):
                class2info[node_class]['node_layers'][0] = weakref.proxy(self)

        ## 2) connect parents in class2info
        for node_class, parent_list in static_lineage.items():
            node_info = class2info[node_class]
            if 'parents' not in node_info:
                node_info['parents'] = [[] for _ in range(len(parent_list))]
            for layer_id in range(node_info['num_layers']):
                for parent_id, parent_group in enumerate(parent_list):
                    parent_class, parent_layer_id = parent_group[layer_id]
                    parent_info = class2info[parent_class]
                    node_info['parents'][parent_id].append(parent_info['node_layers'][parent_layer_id])

        ## 3) create variable _graph as a dictionary: 
        # {
        #   node instance: {
        #       'class': NodeType, 'parents': [...], 'layer_id': int,
        #       'quantum': bool, 'root': bool
        #   }
        # }
        graph = Graph()
        for node_class, node_info in class2info.items():
            for layer_id, node in enumerate(node_info['node_layers']):
                graph[node] = {
                    'class': node_class,
                    'node': node,
                    'parents': [],
                    'layer_id': layer_id,
                    'quantum': node_info['num_layers'] > 1,
                    'root': len(node_info['parents']) == 0,
                }
                for parent_groups in node_info['parents']:
                    graph[node]['parents'].append(parent_groups[layer_id])

        ## 4) broadcast _graph to every existing node (nodes weakly link to graph)
        for node in graph.nodes():
            if node == self:
                node._graph = graph
            else:
                node._graph = weakref.proxy(graph)

        ## 5) initialize all graphs
        for node in graph.nodes():
            node._initialize_node()

    def forward(self):
        # root doesn't need forward
        return self._is_root

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
                    # update the parent state in NodeCI
                    assert hasattr(node, '_parents_alive')
                    setattr(node, '_parents_alive', parent_states)
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
                node = parent.retr(node_name)
                if node:
                    break
            return node
        else:
            return None

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
        node_set = list()
        ## 1) Collect all node instances
        for node, node_info in self._graph.items():
            if mode == 'surface' and node_info['layer_id'] > 0:
                continue
            else:
                node_set.append(node)

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
        self.broadcasting.update(message)

    def traverse(self, callback):
        """
        run callback() in all node nodes of the graph
        """
        return self._traverse_graph(callback, mode='surface')

    @property
    def broadcasting(self):
        return self._graph._notice_board


    #
    # Graph drawing related
    #
    def _get_node_attribute(self, node):
        if node._is_root:
            return {'fillcolor': '.95, .5, 1.', 'style': 'filled, rounded'}
        elif node._is_quantum:
            return {'fillcolor': '.65 .5 1.', 'style': 'filled,dashed,rounded', 'fontcolor': 'white', 'penwidth': '1.5'}
        elif isinstance(node, NodeCI):
            return {'fillcolor': '.4 .5 1.', 'style': 'filled,rounded'}
        else:
            return {'style': 'rounded'}

    def _get_edge_attribute(self, parent, child):
        if isinstance(child, NodeCI):
            return {'style': 'dashed'}
        else:
            return {}

    def draw_graph(self, curve_edges=False):
        from graphviz import Digraph
        g = Digraph('G', filename='graph')
        g.attr('node', shape='box')
        g.graph_attr['splines'] = 'true' if curve_edges else 'false'

        # collect nodes and edges
        nodes, edges = dict(), dict()
        all_nodes = self._traverse_graph(lambda node: node, mode='complete')
        for node in all_nodes:
            nodes[str(node)] = self._get_node_attribute(node)
            for parent in node._parents:
                edges[(str(parent), str(node))] = self._get_edge_attribute(parent, node)

        # draw nodes and edges
        for node_str, node_attr in nodes.items():
            g.node(node_str, **node_attr)
        for (parent_str, node_str), edge_attr in edges.items():
            g.edge(parent_str, node_str, **edge_attr)

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
    def _initialize_node(self):
        self._parents_alive = [True for _ in self._parents]

    @property
    def parent_list(self):
        new_parents = []
        for parent, alive in zip(self._parents, self._parents_alive):
            new_parents.append(parent if alive else None)
        return new_parents
