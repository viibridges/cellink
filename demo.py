from graph import Input

#
# draw graph
#
root = Input()
root.draw_graph()


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