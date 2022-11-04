import weakref
import copy
import uuid
import hashlib
from graphviz import Digraph

from .registry import registry
from .graph import Graph

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

        # dynamic states, to record if an node node being forwarded
        # _forward_state is a dictionary of boolean values: 
        self._forward_state = {'visited': False, 'success': False}

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

    @property
    def _quantum_num(self):
        """ Return number of quantums (layers) of current node """
        return self._graph[self]['num_layers']

    @property
    def _quantum_id(self):
        """ Return the order number of current node, start from 0 """
        return self._graph[self]['layer_id']

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

            # allowing layer broadcasting if parent_group has only one single-layer parent
            # ie. @hook_parent(Node1, [Node2, Node3], Node4)
            max_parent_layers = 0 if len(new_parent_list) == 0 else max(len(grp) for grp in new_parent_list)
            if max_parent_layers > 1:
                for parent_group in new_parent_list:
                    if len(parent_group) == 1:
                        # duplicate parent layer to match the maximum of parent layers
                        parent_class, idx = parent_group[0]
                        parent_group.extend([(parent_class, idx) for _ in range(1,max_parent_layers)])

            # check the number of parent layers to secure matches
            parent_layer_nums = set(len(grp) for grp in new_parent_list)
            assert len(parent_layer_nums) in [0, 1], "Parent layer number mismatches: {}".format(node_class)

            static_lineage[node_class] = new_parent_list

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
        #       'class': NodeType, 'parents': [...],
        #       'num_layers': int, 'layer_id': int,
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
                    'num_layers': len(node_info['node_layers']),
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
        if not self._forward_state['visited']:
            success = self.forward()
            # node.forward() has been run, mark this node as visited
            self._forward_state['visited'] = True
            if success not in [True, False]:
                raise RuntimeError(
                    "{} forward() should return either 'True' or 'False', "
                    "while it returns: {}".format(type(self), success)
                )
            else:
                self._forward_state['success'] = success

    def _forward_to_node(self, node):
        """
        Run a sequence of forward methods towards the target node (included)
        """
        if not node._forward_state['visited']:
            ## 1) parepare to run (try to visit all parents)
            # if current node is NodeCI, keep forwarding as lone as it has >= one parent return True
            if isinstance(node, NodeCI):
                list(map(self._forward_to_node, node._parents))
                if all([not parent._forward_state['success'] for parent in node._parents]):
                    return

            # if current node is NodeNI, keep forwarding as lone as its parent is visited but
            # forward state is False (acting as a NOT node)
            elif isinstance(node, NodeNI):
                assert len(node._parents) == 1
                parent = node._parents[0]
                self._forward_to_node(parent)
                if not parent._forward_state['visited'] or parent._forward_state['success']:
                    return

            # if current node is NodeSI or NodeMI, stop if any one of the parents is not seakable
            # or return False
            else:
                for parent in node._parents:
                    self._forward_to_node(parent)
                    if not parent._forward_state['success']:  # immediate stop if one dead parent found
                        return

            ## 2) run forward
            node._run_forward()

    def seek(self, node_name:str):
        """
        reach node by executing series of forward() methods.
        NOTE: unlike method retr(), seek() can start from any node

        Args:
            node_name: a string, name of the node to return

        Return:
            the node object with the node_name
        """
        target_node = self[node_name]
        self._forward_to_node(target_node)
        return target_node if target_node._forward_state['success'] else None

    def _run_backward(self):
        success = self.backward()
        if success not in [True, False]:
            raise RuntimeError(
                "{} backward() should return either 'True' or 'False', "
                "while it returns: {}".format(type(self), success)
            )
        else:
            return success

    def _backward_from_node(self, source_node, target_node=None):
        """
        Run a sequence of backwards methods from node towards the target node (node_name)
        """
        # find the node
        if target_node and source_node == target_node:
            return source_node

        # keep scanning upwards
        elif source_node._run_backward():
            reached_node = None
            for parent in source_node._parents:
                source_node = self._backward_from_node(parent, target_node)
                if source_node:
                    reached_node = source_node
            return reached_node
        return None

    def retr(self, node_name:str=None):
        """
        reach node in a bottom-up manner by executing series of backward() methods

        Args:
            node_name: a string, name of the node to return

        Return:
            the node object with the node_name
        """
        target_node = self[node_name] if node_name else None
        return self._backward_from_node(self, target_node)

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

    def __getitem__(self, node_name):
        # allow the trival case: node[node] == node
        if isinstance(node_name, NodeBase):
            return node_name

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
        elif isinstance(node, NodeNI):
            return {'fillcolor': '.1 .5 1.', 'style': 'filled,rounded'}
        else:
            return {'style': 'rounded'}

    def _get_edge_attribute(self, parent, child):
        if isinstance(child, NodeCI):
            return {'style': 'dashed'}
        else:
            return {}

    def draw_graph(self, splines='curved'):
        g = Digraph('G', filename='graph')
        g.attr('node', shape='box')

        legal_edge_styles = ['line', 'curved', 'spline', 'polyline', 'ortho']
        assert splines in legal_edge_styles, \
            "'splines' must be one of the following style: {}".format(legal_edge_styles)

        g.graph_attr['splines'] = splines

        # collect nodes and edges
        nodes, edges = dict(), dict()
        all_nodes = self._traverse_graph(lambda node: node, mode='complete')
        for node in all_nodes:
            nodes[str(node)] = self._get_node_attribute(node)
            for parent_id, parent in enumerate(node._parents):
                edges[(str(parent), str(node), parent_id)] = self._get_edge_attribute(parent, node)

        # draw nodes and edges
        for node_str, node_attr in nodes.items():
            g.node(node_str, **node_attr)
        for (parent_str, node_str, _), edge_attr in edges.items():
            g.edge(parent_str, node_str, **edge_attr)

        g.render(view=False, cleanup=True)


class NodeSI(NodeBase):
    """
    Definition of nodes that have only one parent
    """
    def _initialize_node(self):
        assert len(self._parents) in [0,1], \
            "NodeSI accept only one parent, but {} found".format(len(self._parents))

    @property
    def parent(self):
        return self._parents[0]

class NodeMI(NodeBase):
    """
    Logical AND node:
    Definition of nodes that have more than one parents;
    Seekable when all its parents are seekable
    """
    @property
    def parent_list(self):
        return self._parents

class NodeCI(NodeBase):
    """
    Logical OR node:
    Definition of nodes that have more than one parents;
    Seekable if any one of its parents is seekable
    """
    def _initialize_node(self):
        assert len(self._parents) > 0, \
            "NodeCI accept one or more parents, but {} found".format(len(self._parents))

    @property
    def parent_list(self):
        new_parents = []
        for parent in self._parents:
            seekable = parent._forward_state['success']
            new_parents.append(parent if seekable else None)
        return new_parents

class NodeNI(NodeBase):
    """
    Logical NOT node:
    Definition of nodes that have only one parent, and only seekable 
    when its parent is seekable and the forward method returns False
    """
    def _initialize_node(self):
        assert len(self._parents) == 1, \
            "NodeNI accept only one parent, but {} found".format(len(self._parents))

    @property
    def parent(self):
        return self._parents[0]