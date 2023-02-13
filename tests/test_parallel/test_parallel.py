from graph import *

class Test:
    def test_static(self):
        root = Root()
        root.draw_graph(splines='spline')
        root.seek('V')