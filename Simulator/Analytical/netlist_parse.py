import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

def plot_graph_old(instance_dict, net_dict):
    G = nx.MultiDiGraph()
    size = 5
    spacing = 100
    pos = {}
    for instance in instance_dict:
        G.add_node(instance)
    for net in net_dict:
        [u,v] = net_dict[net]
        G.add_edge(u,v,label=net)
    for instance in instance_dict:
        name = instance[2:]
        inst_num = int(name)
        if inst_num < size**2:
            x = (inst_num%size)*spacing
            y = (inst_num//size)*-1*spacing
        else:
            if inst_num < size**2 + size:
                x = -1*spacing
                y = (inst_num-size**2)*-1*spacing
            else:
                x = (inst_num-size**2-size)*spacing
                y = (size+1)*-1*spacing
        pos[instance] = (x,y)

    # print(G.edges.data(keys=True))
    # nx.draw_networkx(G, pos=pos, with_labels=True, node_shape='s', node_size=500, connectionstyle='arc3,rad=0.2')

    fig, ax = plt.subplots()
    for e in G.edges:
        txt = G.edges[e[0],e[1], e[2]]['label']
        x = 0.5*(pos[e[0]][0] + pos[e[1]][0])
        y = 0.5*(pos[e[0]][1] + pos[e[1]][1])
        xy = pos[e[0]]
        xy_t = pos[e[1]]
        if pos[e[0]][0] == pos[e[1]][0]:
            x -= 30*e[2]
            xy = (pos[e[0]][0], min(pos[e[0]][1], pos[e[1]][1]))
            xy_t = (pos[e[0]][0], max(pos[e[0]][1], pos[e[1]][1]))
        if pos[e[0]][1] == pos[e[1]][1]:
            y += 30*e[2]
            xy = (min(pos[e[0]][0], pos[e[1]][0]), pos[e[0]][1])
            xy_t = (max(pos[e[0]][0], pos[e[1]][0]), pos[e[0]][1])
        txt_loc = (x,y)
        ax.annotate(f"",
                    xy=xy, xycoords='data',
                    xytext=xy_t, textcoords='data',
                    arrowprops=dict(arrowstyle="-", color='lightblue',
                                    shrinkA=5, shrinkB=5,
                                    patchA=None, patchB=None,
                                    connectionstyle="arc3,rad=rrr".replace('rrr',str(0.3*e[2])
                                    ),
                                    ),
                    )
        ax.annotate(txt,
                    xy=txt_loc, xycoords='data',
                    )
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=500, node_shape='s')
    nx.draw_networkx_labels(G, pos, {name:name for name in G.nodes}, ax=ax)
    fig.set_size_inches((10,7.5))
    plt.box(False)
    plt.show()

def plot_graph(instance_dict, net_dict, activity_dict={}, triggered_instances=set()):
    G = nx.MultiDiGraph()
    size = 5
    spacing = 100
    pos = {}
    # triggered_instances = {'xi0', 'xi1'}
    # activity_dict = {'enable<0>': (3, 1, 'r'), 'enable<1>': (4, 1, 'r'), 'enable<2>': (1, 1, 'r'), 'enable<3>': (2, 1, 'r'), 'enable<4>': (5, 1, 'r')}
    node_color = []
    for instance in instance_dict:
        G.add_node(instance)
        if instance in triggered_instances:
            node_color.append('r')
        else:
            node_color.append('b')
    for net in net_dict:
        [u,v] = net_dict[net]
        G.add_edge(u,v,label=net)
    for instance in instance_dict:
        name = instance[2:]
        inst_num = int(name)
        if inst_num < size**2:
            x = (inst_num%size)*spacing
            y = (inst_num//size)*-1*spacing
        else:
            if inst_num < size**2 + size:
                x = -1*spacing
                y = (inst_num-size**2)*-1*spacing
            else:
                x = (inst_num-size**2-size)*spacing
                y = (size+1)*-1*spacing
        pos[instance] = (x,y)
    
    fig, ax = plt.subplots()
    for e in G.edges:
        txt = G.edges[e[0],e[1], e[2]]['label']
        x = 0.5*(pos[e[0]][0] + pos[e[1]][0])
        y = 0.5*(pos[e[0]][1] + pos[e[1]][1])
        xy = pos[e[0]]
        xy_t = pos[e[1]]
        if pos[e[0]][0] == pos[e[1]][0]:
            x -= 30*e[2]
            xy = (pos[e[0]][0], min(pos[e[0]][1], pos[e[1]][1]))
            xy_t = (pos[e[0]][0], max(pos[e[0]][1], pos[e[1]][1]))
        if pos[e[0]][1] == pos[e[1]][1]:
            y += 30*e[2]
            xy = (min(pos[e[0]][0], pos[e[1]][0]), pos[e[0]][1])
            xy_t = (max(pos[e[0]][0], pos[e[1]][0]), pos[e[0]][1])
        txt_loc = (x,y)
        if txt in activity_dict:
            edge_color = 'red'
        else:
            edge_color = 'lightblue'
        ax.annotate(f"",
                    xy=xy, xycoords='data',
                    xytext=xy_t, textcoords='data',
                    arrowprops=dict(arrowstyle="-", color=edge_color,
                                    shrinkA=5, shrinkB=5,
                                    patchA=None, patchB=None,
                                    connectionstyle="arc3,rad=rrr".replace('rrr',str(0.3*e[2])
                                    ),
                                    ),
                    )
        ax.annotate(txt,
                    xy=txt_loc, xycoords='data',
                    )
    nodes = nx.draw_networkx_nodes(G, pos, ax=ax, node_size=500, node_shape='s', node_color=node_color)
    node_labels = nx.draw_networkx_labels(G, pos, {name:name for name in G.nodes}, ax=ax)
    fig.set_size_inches((10,7.5))
    plt.box(False)
    plt.show()

def build_subckt(subckt_name, subckt_portlist, fileobj):
    for line in fileobj:
        line_arr = line.split()
        if line_arr[0] == '.ends':
            return
        
def netlist_parse(fname, ignore_nets):
    with open(fname) as f:
        subckt_dict = {}
        instance_dict = {}
        net_dict = {}
        # Skip first line unconditionally for SPICE netlists
        for i in range(1):
            next(f)
        for line in f:
            line_lc = line.lower() 
            line_arr = line_lc.split()
            # skip empty or commented lines
            if len(line_arr) == 0 or line_arr[0][0] == '*':
                continue
            # print(line_arr)
            # Read subckt and store in dict
            if line_arr[0] == '.subckt':
                subckt_name = line_arr[1]
                subckt_portlist = line_arr[2:]
                subckt_portlist_noPG = []
                for port in subckt_portlist:
                    if port not in ignore_nets:
                        subckt_portlist_noPG.append(port)
                build_subckt(subckt_name, subckt_portlist_noPG, f)
                subckt_dict[subckt_name] = subckt_portlist_noPG
                # print(f"Finished reading {subckt_name}")
            # Read instance and store in dict
            # Read nets and store in dict
            if line_lc[0] == 'x':
                instance_name = line_arr[0]
                subckt_type = line_arr[-1]
                port_list = line_arr[1:-1]
                port_list_noPG = []
                for port in port_list:
                    if port not in ignore_nets:
                        port_list_noPG.append(port)
                if len(port_list_noPG) != len(subckt_dict[subckt_type]):
                    raise SyntaxError(f"{instance_name} of type {subckt_type} has {len(port_list_noPG)} ports but needs {len(subckt_dict[subckt_type])}")
                port_map = {}
                # Port map uses subckt port as key and a netname as value
                # as a port cannot be connected to more than one net
                for subckt_port, netname in zip(subckt_dict[subckt_type], port_list_noPG):
                    port_map[subckt_port] = netname
                instance_dict[instance_name] = (subckt_type, port_map)
                for net in port_list_noPG:
                    if net not in net_dict:
                        net_dict[net] = []
                    net_dict[net].append(instance_name)

    return subckt_dict, instance_dict, net_dict

if __name__ == '__main__':
    subckt_dict, instance_dict, net_dict = netlist_parse('./ising_50x50.sp', ['vdd', 'vss'])
    #for subckt in subckt_dict:
    #    print(f"{subckt}: {subckt_dict[subckt]}")
    #print("### INSTANCE DICT")
    #for instance in instance_dict:
    #    print(f"{instance}: {instance_dict[instance]}")
    #print("### NET DICT")
    #for net in net_dict:
    #    print(f"{net}: {net_dict[net]}")
    #plot_graph(instance_dict, net_dict)
    node_set = []
    i = 0
    for instance_num in range(2450, 2500):
        portmap = instance_dict[f'xi{instance_num}'][1]
        #print(f"xi{instance_num} {portmap['l2r_in']} {portmap['d2u_in']}")
        print(f"(0, {i}): ('{portmap['l2r_in']}', '{portmap['d2u_in']}'),")
        i += 1
        node_set.append(portmap['l2r_in']) 
        node_set.append(portmap['d2u_in'])
    node_set = set(node_set)
    print(node_set)
