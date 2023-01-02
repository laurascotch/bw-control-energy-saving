import networkx as nx
import pycurl
import json
from io import BytesIO
import re
import matplotlib.pyplot as plt

G = nx.Graph()

def get_all_hosts(switches):
    swport_hosts = {}   # {'switch_port':'host_mac'}
    host_per_switch = {}

    for switch in switches:
        dpid = str(switch).rjust(16, '0')

        b_obj = BytesIO()
        crl = pycurl.Curl()
        url = f"http://localhost:8080/v1.0/topology/hosts/{dpid}"
        crl.setopt(crl.URL, url)
        crl.setopt(crl.WRITEDATA, b_obj)

        crl.perform()
        crl.close()

        get_body = b_obj.getvalue()
        raw_hosts = json.loads(get_body.decode('utf8'))

        hosts = []

        host_no = 0
        
        for h in raw_hosts:
            #if len(h["ipv4"])==0:   # the connected host without IP should be the controller, ignore it
            #    continue
            host_mac = h["mac"]
            port = (h["port"]["name"]).lstrip('0')
            if(port) not in swport_hosts.keys():
                host_no += 1
            swport_hosts[port] = host_mac

        host_per_switch[str(switch)] = host_no

    return swport_hosts, host_per_switch

# ce l'ho
def get_all_switches():
    b_obj = BytesIO()
    crl = pycurl.Curl()

    crl.setopt(crl.URL, 'http://localhost:8080/stats/switches')
    crl.setopt(crl.WRITEDATA, b_obj)

    crl.perform()
    crl.close()

    get_body = b_obj.getvalue()
    raw_sw = json.loads(get_body.decode('utf8'))

    switches = []
    #sw_dpid = []

    for s in raw_sw:
        #dpid = str(s).rjust(16, '0')
        #switches.append(dpid)
        switches.append(str(s))

    return switches


def switch_off_unrouted(switch_off, links):
    links_to_delete = []
    for s in switch_off:
        for l,ports in links.items():
            port = ports.split(',')
            s0 = re.match("s(\d+)?-eth(\d+)?",port[0])
            s1 = re.match("s(\d+)?-eth(\d+)?",port[1])
            dpid0 = s0[1]
            portno0 = s0[2]
            dpid1 = s1[1]
            portno1 = s1[2]
            if dpid0 == s:
                url = f"http://localhost:8080/stats/portdesc/modify"
                data0 = json.dumps({"dpid": dpid0, "port_no":portno0, "config": 1, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta
                data1 = json.dumps({"dpid": dpid1, "port_no":portno1, "config": 1, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta
                crl = pycurl.Curl()
                crl.setopt(pycurl.POST, 1)
                crl.setopt(crl.URL, url)
                crl.setopt(crl.POSTFIELDS, data0)
                crl.setopt(crl.VERBOSE, 1)

                crl.perform()
                crl.close()

                crl = pycurl.Curl()
                crl.setopt(pycurl.POST, 1)
                crl.setopt(crl.URL, url)
                crl.setopt(crl.POSTFIELDS, data1)
                crl.setopt(crl.VERBOSE, 1)

                crl.perform()
                crl.close()
                links_to_delete.append(l)
            if dpid1 == s:
                url = f"http://localhost:8080/stats/portdesc/modify"
                data0 = json.dumps({"dpid": dpid0, "port_no":portno0, "config": 1, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta
                data1 = json.dumps({"dpid": dpid1, "port_no":portno1, "config": 1, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta
                crl = pycurl.Curl()
                crl.setopt(pycurl.POST, 1)
                crl.setopt(crl.URL, url)
                crl.setopt(crl.POSTFIELDS, data0)
                crl.setopt(crl.VERBOSE, 1)

                crl.perform()
                crl.close()

                crl = pycurl.Curl()
                crl.setopt(pycurl.POST, 1)
                crl.setopt(crl.URL, url)
                crl.setopt(crl.POSTFIELDS, data1)
                crl.setopt(crl.VERBOSE, 1)

                crl.perform()
                crl.close()
                links_to_delete.append(l)
    for l in links_to_delete:
        del links[l]
    
    return links, links_to_delete


def shut_links(links,new_links):
    new_links_str = {}
    for link in new_links:
        link_str = f"s{link[0]},s{link[1]}"
        link_str_reverse = f"s{link[1]},s{link[0]}"
        if link_str in links.keys():
            new_links_str[link_str] = links[link_str]
            del links[link_str]
        if link_str_reverse in links.keys():
            new_links_str[link_str_reverse] = links[link_str_reverse]
            del links[link_str_reverse]
    for l,ports in links.items():
        port = ports.split(',')
        s0 = re.match("s(\d+)?-eth(\d+)?",port[0])
        s1 = re.match("s(\d+)?-eth(\d+)?",port[1])
        dpid0 = s0[1]
        portno0 = s0[2]     # we just need to disable one side of the link because links are "double" (e.g. we have both s1,s2 and s2,s1)
        url = f"http://localhost:8080/stats/portdesc/modify"

        data0 = json.dumps({"dpid": dpid0, "port_no":portno0, "config": 1, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta
        
        crl = pycurl.Curl()
        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data0)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()
    return new_links_str


def bfs_stp():
    # ========== get switches and hosts from controller ==========
    switches = get_all_switches()
    switches.sort()
    sw_hosts, host_per_switch = get_all_hosts(switches)
    # ==============================

    # ========== add nodes (switches) to the graph ==========
    for s in switches:
        G.add_node(s)
    # ==============================

    # ========== get links from controller ==========
    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, 'http://localhost:8080/v1.0/topology/links')
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.perform()
    crl.close()

    get_body = b_obj.getvalue()
    raw_data = json.loads(get_body.decode('utf8'))
    
    links = {}  # here we save which ports create the link in the form of: 's1,s2': 's1-eth1,s2-eth1'

    for entry in raw_data:
        s1 = entry['src']['dpid'].lstrip('0')
        p1 = entry['src']['name']
        s2 = entry['dst']['dpid'].lstrip('0')
        p2 = entry['dst']['name']
        G.add_edge(s1,s2)
        edge = f"s{s1},s{s2}"
        links[edge] = f"{p1},{p2}"
    # ==============================

    # ========== build a tree from the graphs so to break the loops ==========
    # each node/switch is given a value based on the connections to other switches
    # and number of connected hosts. The bfs tree will start from the node with the
    # highest score. This way, it is more likely that switches with no hosts connected
    # will become leaves. Those switches can be shut down since no traffic will ever
    # need to pass there.
    bfs_value = {}
    for s in switches:
        s_degree = G.degree[s]
        bfs_value[s] = s_degree * 2 + host_per_switch[s]
    bfs_origin = max(bfs_value, key=bfs_value.get)

    # "optimized spanning tree"
    T = nx.bfs_tree(G,bfs_origin)
    new_links = list(T.edges())

    # shut unwanted links
    links = shut_links(links,new_links)

    # if a leaf switch has no hosts attached, it can be turned off
    # let's find them:
    switch_off = [x for x in T.nodes() if T.out_degree(x)==0 and host_per_switch[x]==0]
    # to do: disable all ports of the found switches
    links, remove_edges = switch_off_unrouted(switch_off, links)
    for e in remove_edges:
        m = re.match("s(\d+)?,s(\d+)?",e)
        e1 = (m[1],m[2])
        e2 = (m[2],m[1])
        if e1 in T.edges():
            T.remove_edge(*e1)
        if e2 in T.edges():
            T.remove_edge(*e2)
    # ==============================
    original_network = G.to_undirected()
    # ========== populate the tree graph with hosts and compute flows ==========
    hosts = []
    ports_to_hosts = []
    edges_to_hosts = []
    for port,host in sw_hosts.items():
        m = re.match("s(\d+)?-eth(\d+)?",port)
        s = m[1]
        p = m[2]
        hosts.append(host)
        e = (s,host)
        edges_to_hosts.append(e)
        T.add_node(host)
        T.add_edge(s,host)
        original_network.add_node(host)
        original_network.add_edge(s,host)
        ports_to_hosts.append(port)
    
    network = T.to_undirected()

    edges = original_network.edges()
    stp_edges = network.edges()
    node_colors = []
    for n in original_network.nodes():
        if n in switch_off:
            node_colors.append('slategrey')
            continue
        if n in hosts:
            node_colors.append('lightblue')
            continue
        node_colors.append('tab:blue')
        
    colors = []
    weights = []
    labels = {}
    for n in original_network.nodes():
        if n in hosts:
            labels[n] = ''
        else:
            labels[n]=n
    for e in edges:
        if e in edges_to_hosts:
            colors.append('c')
            weights.append(2)
            continue
        if e in stp_edges:
            colors.append('b')
            weights.append(4)
            continue
        colors.append('k')
        weights.append(1)
        
    nx.draw(original_network, edgelist=edges, edge_color=colors, width=weights, node_color=node_colors, labels=labels, with_labels=True)
    plt.show()

    #flows = []
    # now we can compute paths between each other host
    #for host in hosts:
    #    paths = nx.single_source_shortest_path(network,host)
        # must delete paths to switches and maintain only those to hosts
        # after having all paths, we can populate the ryu flow tables for each switch
    # ==============================

    return links, ports_to_hosts, switch_off, network