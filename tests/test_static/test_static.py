from graph import *

class Test:
    def test_static(self):
        root = Node1()
        node1 = root.seek('node1c')
        node2 = root.seek('node2c')
        assert np.all(node1.quantum_mat == node2.quantum_mat)
        assert np.all(node1.shared_mat == node2.shared_mat)
        assert np.all(node1.rand_mat != node2.rand_mat)