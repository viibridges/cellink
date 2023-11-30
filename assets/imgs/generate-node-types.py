# Let's write the Graphviz code for two flowcharts side by side with the specified properties.

# pip install pygraphviz
import pygraphviz as pgv

# Define the graph
B = pgv.AGraph(directed=True, rankdir='TB', compound=True)

with B.subgraph(name='cluster1') as c:
    c.graph_attr['color']='none'
    c.add_node('input1', shape='box', style='rounded', label='...')
    c.add_node('NodeSI', shape='box', style='rounded')
    c.add_node('output1', shape='box', style='rounded', label='...')
    c.add_edge('input1', 'NodeSI')
    c.add_edge('NodeSI', 'output1')

with B.subgraph(name='cluster2') as c:
    c.graph_attr['color']='none'
    c.add_node('input2a', shape='box', style='rounded', label='...')
    c.add_node('input2b', shape='box', style='rounded', label='...')
    c.add_node('NodeMI', shape='box', style='rounded')
    c.add_node('output2', shape='box', style='rounded', label='...')
    c.add_edge('input2a', 'NodeMI')
    c.add_edge('input2b', 'NodeMI')
    c.add_edge('NodeMI', 'output2')

with B.subgraph(name='cluster3') as c:
    c.graph_attr['color']='none'
    c.add_node('input3a', shape='box', style='rounded', label='...')
    c.add_node('input3b', shape='box', style='rounded', label='...')
    c.add_node('NodeCI', shape='box', style='rounded, filled', fillcolor='.4 .5 1')
    c.add_node('output3', shape='box', style='rounded', label='...')
    c.add_edge('input3a', 'NodeCI', style='dashed')
    c.add_edge('input3b', 'NodeCI', style='dashed')
    c.add_edge('NodeCI', 'output3')

with B.subgraph(name='cluster4') as c:
    c.graph_attr['color']='none'
    c.add_node('input4', shape='box', style='rounded', label='...')
    c.add_node('NodeNI', shape='box', style='rounded, filled', fillcolor='.1 .5 1')
    c.add_node('output4', shape='box', style='rounded', label='...')
    c.add_edge('input4', 'NodeNI')
    c.add_edge('NodeNI', 'output4')

with B.subgraph(name='cluster5') as c:
    c.graph_attr['color']='none'
    c.add_node('input5', shape='box', style='rounded', label='...')
    with c.subgraph(name='clusterPI') as d:
        d.graph_attr['color']='none'
        d.graph_attr['fillcolor']='lightyellow'
        d.graph_attr['pencolor']='lightgrey'
        d.graph_attr['style']='rounded, filled'
        d.add_node('NodePI1', shape='box', style='rounded, filled', fillcolor='white', label='NodePI')
        d.add_node('NodePI2', shape='box', style='rounded, filled', fillcolor='white', label='NodePI')
    c.add_edge('input5', 'NodePI1')
    c.add_edge('NodePI1', 'NodePI2', style='invis')

# Save the dot file and also render as a png to visually verify
B.draw('node-types.png', format='png', prog='dot')
