from .registry import registry
import weakref


class Family(object):
    def __init__(self):
        # node node object container, to keep track of the edges of the graph
        # each node saves only its parents and the children
        self.parents  = []
        self.children = []

        # dynamic states, to record if an node node being forwarded/backwarded
        # None: unvisited, True: forward succeeded, False: forward failed
        self.forward_state = None

    @property
    def isroot(self):
        return len(self.parents) == 0



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
        # TODO: comments
        self._families = [Family()]

        # TODO: comments
        self._family_index = {'prev': 0, 'curr': 0, 'next': 0}

        # start building the graph
        if bootstrap_node:
            self._build_graph(dict())
            self._check_graph()

            # notice board, on which messages are synchronized/updated across all nodes
            #  in the graph, when calling broadcast() method from any node
            notice_board = dict()
            self._traverse_graph(lambda node: node.__setattr__('_notice_board', notice_board))

    @property
    def _parents(self):
        idx = self._family_index['curr']
        return self._families[idx].parents

    @property
    def _children(self):
        idx = self._family_index['curr']
        return self._families[idx].children

    @property
    def _forward_state(self):
        idx = self._family_index['curr']
        return self._families[idx].forward_state

    def _set_forward_state(self, state):
        idx = self._family_index['curr']
        self._families[idx].forward_state = state

    @property
    def isroot(self):
        return len(self._families) == 1 and self._families[0].isroot

    def __str__(self):
        return type(self).__name__

    def _initialize(self):
        raise NotImplementedError()

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

        ## 1) register child-subgraph
        for child_cls in registry[type(self)].children:
            if child_cls not in visited_nodes:
                child = child_cls(bootstrap_node=False)
                child._build_graph(visited_nodes)
                # print("{} builds child {}".format(self, child))
            else:
                child = visited_nodes[child_cls]
            self._children.append(child)

        ## 2) register parent-subgraph
        for parent_cls in registry[type(self)].parents:
            if parent_cls not in visited_nodes:
                parent = parent_cls(bootstrap_node=False)
                parent._build_graph(visited_nodes)
                # print("{} builds parent {}".format(self, parent))
            else:
                parent = visited_nodes[parent_cls]
            self._parents.append(parent)

        self._initialize()

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
                self._set_forward_state(success)
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
        assert len(self._parents) in [0, 1]  # 0 for root node case
        self.parent = None if len(self._parents) == 0 else self._parents[0]

class NodeMI(NodeBase):
    def _initialize(self):
        self.parent_list = self._parents

class NodeCI(NodeBase):
    def _initialize(self):
        self.parent_list = self._parents
