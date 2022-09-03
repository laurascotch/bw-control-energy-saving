import networkx as nx
import pycurl
import json
from io import BytesIO

G = nx.Graph()

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

if __name__ == "__main__":
    switches = get_all_switches()

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

    print(links)