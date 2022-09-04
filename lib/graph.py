class Graph(object):
    """
    Graph class to manage graph info (edge connections etc.)
    """
    def __init__(self):
        self._graph = dict()
        self._notice_board = dict()

    def __setitem__(self, key, val):
        assert isinstance(val, dict)
        assert 'node' in val
        if isinstance(key, str):
            self._graph[key] = val
        else:
            self._graph[key._identity] = val

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._graph[key]
        else:
            return self._graph[key._identity]

    def keys(self):
        return self._graph.keys()

    def values(self):
        return self._graph.values()

    def nodes(self):
        for node_info in self.values():
            yield node_info['node']

    def items(self):
        for node_info in self.values():
            yield node_info['node'], node_info

    def pop(self, key):
        if isinstance(key, str):
            self._graph.pop(key)
        else:
            self._graph.pop(key._identity)