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

node = root.seek('mod10')
print(node.val)