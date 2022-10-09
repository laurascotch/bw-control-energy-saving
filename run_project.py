import pycurl
import json
from io import BytesIO
import time
import re
import matplotlib.pyplot as plt
from bfs_stp import bfs_stp
from initialize_qos import initialize_qos


# ===== GLOBAL DICTIONARIES =====
#previous_pkt_count = {}     # keeps track of packets in flow, to understand whether there's traffic passing or not
previous_bytes = {}     # keeps track of packets in flow, to understand whether there's traffic passing or not
#prev_port_pkt_count = {}
prev_port_bytes = {}
power_per_intf = {'0.0':0, '10.0':0.1, '100.0':0.2, '1000.0':0.5, '10000.0':5.0}     # link rate (Mbps) : power required (W)
BASE_POWER = 20
used_ports = {}     # keeps track of whether a packet flow is going through a certain port over time

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
        switches.append(s)

    return switches


def get_links():
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
        edge = f"s{s1},s{s2}"
        links[edge] = f"{p1},{p2}"
    # ==============================
    return links


def get_switch_ports(switches):
    switch_ports = {}   # { "s1" : ["1", "2", "3"] , "s2" : ["1", "2", "3"] , ... }
    for n in range(len(switches)):
        curl = pycurl.Curl()
        byte_response = BytesIO()

        switch_dpid = f"{n+1}"
        switch_name = f"s{n+1}"
        #energy_required[switch_name] = []

        #flows_per_time[switch_name] = []
        #switch_ports[switch_name] = []

        # get switch ports' numbers
        url=f"http://127.0.0.1:8080/stats/port/{switch_dpid}"

        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, byte_response)
        curl.perform()
        curl.close()

        get_body = byte_response.getvalue()
        json_ports = json.loads(get_body.decode('utf8'))

        #req = requests.request(method='get', url=f'http://127.0.0.1:8080/stats/port/{switch_dpid}')
        #json_ports = req.json()
        ports = json_ports[switch_dpid]
        for port in ports:
            if port['port_no'] != 'LOCAL':
                p = port['port_no']
                if switch_name not in switch_ports.keys():
                    switch_ports[switch_name] = []
                switch_ports[switch_name].append(port['port_no'])

        # initialize flow counter to keep track of in use ports
        tmp = switch_ports[switch_name]
        tmp2 = tmp
        for i in tmp:
            #prev_port_pkt_count[f"{switch_name}-eth{i}"] = 0
            prev_port_bytes[f"{switch_name}-eth{i}"] = 0
            for j in tmp2:
                #previous_pkt_count[f"{switch_name}-{i}-{j}"] = 0
                previous_bytes[f"{switch_name}-{i}-{j}"] = 0
    
    return switch_ports


def get_all_ports(switches):
    ports = []
    
    for s in switches:
        b_obj = BytesIO()
        crl = pycurl.Curl()

        url = f"http://localhost:8080/stats/portdesc/{str(s)}"
        crl.setopt(crl.URL, url)
        crl.setopt(crl.WRITEDATA, b_obj)

        crl.perform()
        crl.close()

        get_body = b_obj.getvalue()
        raw_data = json.loads(get_body.decode('utf8'))
        ports_json = raw_data[str(s)]
        
        for index, port in enumerate(ports_json):
            if index == 0:
                continue
            port_name = port['name']
            ports.append(port_name)
    
    return ports
        

def check_flows():
    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, 'http://localhost:8080/stats/flow/1')
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.perform()
    crl.close()

    get_body = b_obj.getvalue()
    raw_data = json.loads(get_body.decode('utf8'))
    #print(raw_data)
    flows = len(raw_data['1'])

    return flows


def get_ports_speed():
    b_obj = BytesIO()
    crl = pycurl.Curl()

    crl.setopt(crl.URL, 'http://localhost:8080/qos/queue/all')
    crl.setopt(crl.WRITEDATA, b_obj)

    crl.perform()
    crl.close()

    get_body = b_obj.getvalue()

    raw_data = json.loads(get_body.decode('utf8'))

    ports_speed = {}

    prev_id = '0'

    for entry in raw_data:
        if entry['command_result']['result'] == 'success':
            switch_ports = entry['command_result']['details']
            port_names = switch_ports.keys()
            for port in port_names:
                m = re.match("s(\d+)?-eth(\d+)?",port)
                s_id = m[1]
                port_data = ''
                if s_id != prev_id:
                    b_obj = BytesIO()
                    crl = pycurl.Curl()
                    url = f"http://localhost:8080/stats/portdesc/{s_id}"
                    crl.setopt(crl.URL, url)
                    crl.setopt(crl.WRITEDATA, b_obj)
                    crl.perform()
                    crl.close()
                    get_body = b_obj.getvalue()
                    port_data = json.loads(get_body.decode('utf8'))
                speed = switch_ports[port]['0']['config']['max-rate']
                for info in port_data[s_id]:
                    if info['name'] == port:
                        if info['config'] == 1 and info['state'] == 1:
                            speed = '0'
                mbps_speed = int(speed) / (1000 * 1000)
                ports_speed[port] = mbps_speed
    
    return ports_speed


def get_working_ports(switches):

    working_ports = []

    for s in switches:
        switch = f"s{s}"

        curl = pycurl.Curl()
        byte_response = BytesIO()
        
        url=f"http://127.0.0.1:8080/stats/port/{str(s)}"
        
        curl.setopt(curl.CUSTOMREQUEST, 'GET')
        curl.setopt(curl.URL, url)
        #curl.setopt(curl.VERBOSE, 1)
        curl.setopt(curl.WRITEDATA, byte_response)
        
        curl.perform()
        curl.close()
        
        get_body = byte_response.getvalue()
        json_port = json.loads(get_body.decode('utf8'))
        port_stats = json_port[f'{s}']
        for stats in port_stats:
            if stats['port_no'] != 'LOCAL':
                port_name = f"{switch}-eth{stats['port_no']}"
                #port_pkt = stats['rx_packets'] + stats['tx_packets']
                port_bytes = stats['rx_bytes'] + stats['tx_bytes']
                #if port_pkt > prev_port_pkt_count[port_name]:
                if port_bytes > (prev_port_bytes[port_name]+350):
                    #prev_port_pkt_count[port_name] = port_pkt
                    prev_port_bytes[port_name] = port_bytes
                    working_ports.append(port_name)
    
    return working_ports


#def change_link_rate(used_ports,working_ports):
def change_link_rate(working_ports):
    ports_speed = get_ports_speed()
    for port in working_ports:
        used_ports[port] += 1

    #print(used_ports)

    for port in used_ports.keys():
        rate_mbps = 10
        if used_ports[port] > 1:
            rate_mbps = 100
        if used_ports[port] > 3:
            rate_mbps = 1000
        if used_ports[port] > 6:
            rate_mbps = 10000
        if port not in working_ports:
            used_ports[port] = 0
            rate_mbps = 10

        if ports_speed[port] != rate_mbps:
            crl = pycurl.Curl()

            rate = str(rate_mbps * 1000 * 1000)
            dpid = re.match("s(\d+)?-eth\d+",port)[1]
            dpid = dpid.rjust(16, '0')
            url = f"http://localhost:8080/qos/queue/{dpid}"
            data = json.dumps({"port_name": port , "max_rate": "10000000000", "queues": [{"max_rate": rate }]})

            crl.setopt(pycurl.POST, 1)
            crl.setopt(crl.URL, url)
            crl.setopt(crl.POSTFIELDS, data)
            crl.setopt(crl.WRITEFUNCTION, lambda x: None)
            #crl.setopt(crl.VERBOSE, 1)

            crl.perform()
            crl.close()
    


def get_instant_energy():
    ports_speed = get_ports_speed()
    total_network_energy = 0
    switch_energy = {}
    for port in ports_speed.keys():
        switch_dpid = re.match("s(\d+)?-eth\d+",port)[1]
        speed = ports_speed[port]
        total_network_energy = total_network_energy + power_per_intf[str(speed)]
        if switch_dpid not in switch_energy.keys():
            switch_energy[switch_dpid] = 0
        switch_energy[switch_dpid] = switch_energy[switch_dpid] + power_per_intf[str(speed)]
    
    return total_network_energy, switch_energy
    

def energy(switches, links, switch_off):
    # set up
    #switches = get_all_switches()
    switch_ports = get_switch_ports(switches)
    ports = get_all_ports(switches)
    active_links = links
    #print(ports)

    # used_ports = {}
    for p in ports:
        used_ports[p] = 0

    analysis_duration = 600
    count = 0

    energy_per_time = []
    switch_energy_per_time = {}

    try:
        while(count <= analysis_duration):
            # TO DO: check if new run of STP is needed
            actual_links = get_links()
            if actual_links == active_links:
                print("LINKS ARE THE SAME")
            else:
                print("UPDATE NETWORK")
                active_links, switch_off = bfs_stp()
            # TO DO: ottimizzare automaticamente velocità porte
            # usando questa funzione qui per vedere quali stanno lavorando
            working_ports = get_working_ports(switches)
            #change_link_rate(used_ports,working_ports)
            change_link_rate(working_ports)
            t_total_energy_required, t_switch_energy = get_instant_energy()
            energy_per_time.append(t_total_energy_required + BASE_POWER*5)
            
            info = f"t({count}): {t_total_energy_required+BASE_POWER*5} W | working ports: {working_ports}"
            switch_info = ""
            for s, w in t_switch_energy.items():
                switch_info += f"| s{s}: {w+BASE_POWER} "
                if s not in switch_energy_per_time.keys():
                    switch_energy_per_time[s] = []
                switch_energy_per_time[s].append(w + BASE_POWER)
            print(info)
            print(switch_info)
            count += 1
            time.sleep(1)
    except KeyboardInterrupt:
        # risultati finali??
        pass

    fig, ax = plt.subplots()
    ax.hlines(y=BASE_POWER, xmin=0, xmax=len(energy_per_time), color='r', linestyles='--', label='switch base power')
    ax.hlines(y=BASE_POWER*len(switches), xmin=0, xmax=len(energy_per_time), color='lightcoral', linestyles='--', label='total network base power')
    ax.plot(range(len(energy_per_time)), energy_per_time, color='blue', label='total')
    switch_color = {'1':'steelblue', '2':'orchid', '3':'coral', '4':'gold', '5':'yellowgreen'}
    for s in switch_energy_per_time.keys():
        ax.plot(range(len(switch_energy_per_time[s])), switch_energy_per_time[s], color=switch_color[s], label=f's{s}')
    ax.set(xlabel='time unit', ylabel='Power (W)', title='Power required by all switches in network over time')
    plt.legend(loc="upper left")
    ax.set_ylim(ymin=0)
    plt.show()


if __name__ == "__main__":
    # compute BFS STP
    all_links = open("original_links.txt", "w")
    links = get_links()
    for switch_pair,ports in links.items():
        all_links.write(f"{switch_pair}:{ports}\n")
    all_links.close()
    links, switch_off = bfs_stp()   # links: active links, switch_off: switches that can be completely switched off (because nothing is passing through them)
    print("BREAKING LOOPS in TOPOLOGY")
    # wait for it to install (check_flow tables)
    flows = 0
    while flows<3:
        print(".")
        time.sleep(5)
        flows = check_flows()
    # run initial_setup.py
    # run energy while checking for topology changes
    print("NETWORK READY")
    switches = get_all_switches()
    initialize_qos(switches)
    print("READY TO RUN ENERGY OPTIMIZATION SCRIPT")
    energy(switches, links, switch_off)
