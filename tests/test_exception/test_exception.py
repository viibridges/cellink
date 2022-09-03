from graph_exception import Node1

class Test:
    def test_setup(self):
        root = Node1()
        root.draw_graph()

    def test_seek(self):
        root = Node1()
        root.seek('node5')