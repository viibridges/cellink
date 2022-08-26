from graph import Root

#
# draw graph
#
root = Root()
root.draw_graph()


#
# seek
#
root = Root.initialize(42)
node = root.seek('substract')
print(node.val)