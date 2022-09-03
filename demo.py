from graph import Input
from graph import Sqrt

#
# draw graph
#
root = Sqrt()
root.draw_graph()

import pprint
pprint.pprint(root._graph._graph)


#
# seek
#
root = Input.initialize(3)
node = root.seek('plus')
assert node.val == 214

node = root.seek('float-res')
assert node.val == 1

# #
# # triger the garbage collection error caused by weak reference
# #
# def triger_garbage_error():
#     root = Input()
#     return root['plus']
# node = triger_garbage_error()
# print(node)