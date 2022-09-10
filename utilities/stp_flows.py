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


def clean_flows(switches):
    for switch_dpid in switches:
        url = f"http://localhost:8080/stats/flowentry/delete"

        crl = pycurl.Curl()

        #data = json.dumps({"dpid": switch_dpid, "table_id": 1, "match":{"in_port": port_in},"actions":[{"type":"OUTPUT","port":port_out}]})
        data = json.dumps({"dpid": switch_dpid, "table_id": 1})

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()

        data2 = json.dumps({"dpid": switch_dpid, "priority": 0, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": [{"type":"OUTPUT","port":"CONTROLLER"}], "match": {}, "table_id": 1})

        url = f"http://localhost:8080/stats/flowentry/add"

        crl = pycurl.Curl()

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data2)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()


def install_flows(switches,flows):
    clean_flows(switches)
    for flow in flows:
        #flow = [switch_dpid, dl_src, dl_dst, in_port, out_port]
        switch_dpid = flow[0]
        dl_src = flow[1]
        dl_dst = flow[2]
        in_port = (re.match("s\d+-eth(\d+)?",flow[3]))[1]
        out_port = (re.match("s\d+-eth(\d+)?",flow[4]))[1]

        url = f"http://localhost:8080/stats/flowentry/add"

        crl = pycurl.Curl()

        data = json.dumps({"dpid": switch_dpid, "table_id": 1, "idle_timeout": 300, "match":{"in_port": in_port, "dl_src":dl_src, "dl_dst":dl_dst},"actions":[{"type":"OUTPUT","port":out_port}]})

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()


def shut_links(links,new_links):
    to_be_shut = []
    for link in new_links:
        link_str = f"s{link[0]},s{link[1]}"
        if link_str in links.keys():
            del links[link_str]
    for l,ports in links.items():
        port = ports.split(',')
        s0 = re.match("s(\d+)?-eth(\d+)?",port[0])
        s1 = re.match("s(\d+)?-eth(\d+)?",port[1])
        dpid0 = s0[1].rjust(16, '0')
        portno0 = s0[2]
        dpid1 = s1[1].rjust(16, '0')
        portno1 = s1[2]
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


if __name__ == "__main__":
    switches = get_all_switches()
    switches.sort()
    sw_hosts, host_per_switch = get_all_hosts(switches)

    # add nodes
    for s in switches:
        G.add_node(s)

    # get links from controller
    b_obj = BytesIO()
    crl = pycurl.Curl()

    crl.setopt(crl.URL, 'http://localhost:8080/v1.0/topology/links')
    crl.setopt(crl.WRITEDATA, b_obj)

    crl.perform()
    crl.close()

    get_body = b_obj.getvalue()

    raw_data = json.loads(get_body.decode('utf8'))

    print(raw_data)

    links = {}  # here we save which ports create the link in the form of: 's1,s2': 's1-eth1,s2-eth1'

    for entry in raw_data:
        s1 = entry['src']['dpid'].lstrip('0')
        p1 = entry['src']['name']
        s2 = entry['dst']['dpid'].lstrip('0')
        p2 = entry['dst']['name']
        G.add_edge(s1,s2)
        edge = f"s{s1},s{s2}"
        links[edge] = f"{p1},{p2}"

    # now let's add hosts to the network graph
    hosts = []
    for port,host in sw_hosts.items():
        m = re.match("s(\d+)?-eth(\d+)?",port)
        s = m[1]
        p = m[2]
        hosts.append(host)
        G.add_node(host)
        G.add_edge(s,host)
    
    network = G.to_undirected()

    flows = []
    host_to_switch_port = dict((v,k) for k,v in sw_hosts.items())
    # now we can compute paths between each other host
    for host in hosts:
        paths = nx.single_source_shortest_path(network,host)
        #print(paths)    # must delete paths to switches and maintain only those to hosts
        for dest,path in paths.items():
            flow = []   # 0:switch_dpid, 1:dl_src, 2:dl_dst, 3:in_port, 4:out_port
            if dest == host:
                continue
            if dest in switches:
                continue
            for i in range(1,len(path)-1):
                hop = path[i]
                dl_src = host
                dl_dst = dest
                switch_dpid = hop
                in_port = ''
                out_port = ''
                if i==1 and i==(len(path)-2):
                    in_port = host_to_switch_port[host]
                    out_port = host_to_switch_port[dest]
                elif i==1:
                    in_port = host_to_switch_port[host]
                    link_out = f"s{hop},s{path[i+1]}"
                    out_port = links[link_out].split(',')[0]
                elif i==(len(path)-2):
                    link_in = f"s{path[i-1]},s{hop}"
                    in_port = links[link_in].split(',')[1]
                    out_port = host_to_switch_port[dest]
                else:
                    link_in = f"s{path[i-1]},s{hop}"
                    in_port = links[link_in].split(',')[1]
                    link_out = f"s{hop},s{path[i+1]}"
                    out_port = links[link_out].split(',')[0]
                flow = [switch_dpid, dl_src, dl_dst, in_port, out_port]
                flows.append(flow)

    #print(flows)
    install_flows(switches,flows)
        # after having all paths, we can populate the ryu flow tables for each switch