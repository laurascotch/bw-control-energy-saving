import networkx as nx
import pycurl
import json
from io import BytesIO
import re

G = nx.Graph()

def get_all_hosts(switches):
    swport_hosts = {}   # {'switch_port':'host_mac'}
    host_per_switch = {}

    for switch in switches:
        dpid = switch.rjust(16, '0')

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

        host_per_switch[switch] = host_no

    return swport_hosts, host_per_switch


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


def shut_links(links,new_links):
    for link in new_links:
        link_str = f"s{link[0]},s{link[1]}"
        link_str_reverse = f"s{link[1]},s{link[0]}"
        if link_str in links.keys():
            del links[link_str]
        if link_str_reverse in links.keys():
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


if __name__ == "__main__":
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
    shut_links(links,new_links)

    # if a leaf switch has no hosts attached, it can be turned off
    # let's find them:
    switch_off = [x for x in T.nodes() if T.out_degree(x)==0 and host_per_switch[x]==0]
    # to do: disable all ports of the found switches
    # ==============================

    # ========== populate the tree graph with hosts and compute flows ==========
    hosts = []
    for port,host in sw_hosts.items():
        m = re.match("s(\d+)?-eth(\d+)?",port)
        s = m[1]
        p = m[2]
        hosts.append(host)
        T.add_node(host)
        T.add_edge(s,host)
    
    network = T.to_undirected()

    flows = []
    # now we can compute paths between each other host
    for host in hosts:
        paths = nx.single_source_shortest_path(network,host)
        # must delete paths to switches and maintain only those to hosts
        # after having all paths, we can populate the ryu flow tables for each switch
    # ==============================