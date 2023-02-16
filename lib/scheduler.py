#
# scheduler: responsible for task scheduling in parallel runtime
#
from concurrent.futures import ThreadPoolExecutor
import time
import threading

class NodeStatus(object):
    UNVISITED = 0
    RUNNING = 1
    RUNNED = 2
    DEAD = 3

    def __init__(self):
        self._status_dict = dict()

    def __setitem__(self, node, status):
        self._status_dict[node._identity] = status

    def __getitem__(self, node):
        assert node._identity in self._status_dict
        return self._status_dict[node._identity]

    def dump(self):
        status = []
        for key in sorted(self._status_dict.keys()):
            status.append(self._status_dict[key])
        print(status)


class NodeException(object):
    def __init__(self):
        self._exception_dict = dict()

    def __setitem__(self, node, exception):
        self._exception_dict[node._identity] = exception

    def __getitem__(self, node):
        assert node._identity in self._exception_dict
        return self._exception_dict[node._identity]


class Scheduler(object):
    def __init__(self, node_list, max_workers=8):
        self._all_nodes = node_list
        self._status = NodeStatus()
        self._exceptions = NodeException()
        for node in node_list:
            self._status[node] = NodeStatus.UNVISITED
            self._exceptions[node] = None

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.mutex = threading.Lock()

    def prepare_running(self, node):
        self.mutex.acquire()
        self._status[node] = NodeStatus.RUNNING
        self.mutex.release()

    def finish_running(self, node):
        self.mutex.acquire()
        self._status[node] = NodeStatus.RUNNED
        self.mutex.release()

    def kill_running(self, node):
        self.mutex.acquire()
        self._status[node] = NodeStatus.DEAD
        self.mutex.release()

    def query_status(self, node):
        self.mutex.acquire()
        status = self._status[node]
        self.mutex.release()
        return status

    def is_unvisited(self, node):
        return self.query_status(node) == NodeStatus.UNVISITED

    def is_running(self, node):
        return self.query_status(node) == NodeStatus.RUNNING

    def is_dead(self, node):
        return self.query_status(node) == NodeStatus.DEAD

    def is_visited(self, node):
        return not self.is_unvisited(node) and not self.is_running(node)

    def worker(self, node):
        try:
            node._run_forward()
        except Exception as e:
            self._exceptions[node] = e
            self.kill_running(node)
        else:
            self.finish_running(node)

    def submit(self, node):
        self.prepare_running(node)
        self.executor.submit(self.worker, node)

    def run(self):
        while True:
            for node in self._all_nodes:
                if self.is_unvisited(node) and node._ready_to_forward():
                    self.submit(node)

            time.sleep(.005)

            # nodes will never be runned will be marked as DEAD
            for node in self._all_nodes:
                for parent in node._parents:
                    if self.is_dead(parent):
                        self.kill_running(node)
                        break
                if node._forbidden_forwarding():
                    self.kill_running(node)

            # condition to break
            if all(self.is_visited(node) for node in self._all_nodes):
                break

        for node in self._all_nodes:
            exception = self._exceptions[node]
            if exception is not None:
                raise exception

    @classmethod
    def forward_to_nodes(cls, node_list):
        # 1) find all parents of node
        def _get_subtree(node):
            subtree_nodes = [node]
            for parent in node._parents:
                parent_subtree_nodes = _get_subtree(parent)
                subtree_nodes.extend(parent_subtree_nodes)
            return subtree_nodes

        subtree_nodes = list()
        for node in node_list:
            subtree_nodes.extend(_get_subtree(node))

        # 2) remove duplicated nodes
        uuid_set = set()
        filtered_subtree_nodes = []
        for node in subtree_nodes:
            if node._identity not in uuid_set:
                filtered_subtree_nodes.append(node)
                uuid_set.add(node._identity)

        # 3) forward to node in parallel
        scheduler = cls(filtered_subtree_nodes)
        scheduler.run()