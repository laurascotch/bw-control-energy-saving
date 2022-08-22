import pycurl
import json
from io import BytesIO
import time
import re
import matplotlib.pyplot as plt

# ===== GLOBAL DICTIONARIES =====
previous_pkt_count = {}     # keeps track of packets in flow, to understand whether there's traffic passing or not
prev_port_pkt_count = {}
power_per_intf = {'10.0':0.1, '100.0':0.2, '1000.0':0.5, '10000.0':5.0}     # link rate (Mbps) : power required (W)
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
            prev_port_pkt_count[f"{switch_name}-eth{i}"] = 0
            for j in tmp2:
                previous_pkt_count[f"{switch_name}-{i}-{j}"] = 0
    
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

    for entry in raw_data:
        if entry['command_result']['result'] == 'success':
            switch_ports = entry['command_result']['details']
            port_names = switch_ports.keys()
            for port in port_names:
                speed = switch_ports[port]['0']['config']['max-rate']
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
                port_pkt = stats['rx_packets'] + stats['tx_packets']
                if port_pkt > prev_port_pkt_count[port_name]:
                    prev_port_pkt_count[port_name] = port_pkt
                    working_ports.append(port_name)
    
    return working_ports


def slow_get_working_ports():

    working_ports = []

    #previous_pkt_count[f"{switch_name}-{i}-{j}"] = 0

    for sw_in_ex in previous_pkt_count.keys():
        m = re.match("s(\d+)?-(\d+)?-(\d+)?", sw_in_ex)
        switch_dpid = m[1]
        ingress = m[2]
        egress = m[3]
        switch = f"s{switch_dpid}"

        curl = pycurl.Curl()
        byte_response = BytesIO()

        req_body = json.dumps({"out_port":egress, "match":{"in_port":ingress}})
        url = f"http://127.0.0.1:8080/stats/aggregateflow/{switch_dpid}"
        curl.setopt(curl.CUSTOMREQUEST, 'GET')
        curl.setopt(curl.URL, url)
        curl.setopt(curl.POSTFIELDS, req_body)
        #curl.setopt(curl.VERBOSE, 1)
        curl.setopt(curl.WRITEDATA, byte_response)
            
        curl.perform()
        curl.close()

        get_body = byte_response.getvalue()
        json_flow = json.loads(get_body.decode('utf8'))
        flow_stats = json_flow[switch_dpid][0]  # this is a dictionary
        pkt_count = flow_stats["packet_count"]  # maybe also "byte_count" is useful
        if pkt_count>previous_pkt_count[sw_in_ex]:
            previous_pkt_count[sw_in_ex] = pkt_count
            ingress_name = f"{switch}-eth{ingress}"
            egress_name = f"{switch}-eth{egress}"
            working_ports.append(ingress_name)
            working_ports.append(egress_name)
            #print(ingress_name)
            #print(egress_name)
    return list(dict.fromkeys(working_ports))


def change_link_rate(used_ports,working_ports):
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
    

if __name__ == "__main__":
    # set up
    switches = get_all_switches()
    switch_ports = get_switch_ports(switches)
    ports = get_all_ports(switches)
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
            # TO DO: ottimizzare automaticamente velocità porte
            # usando questa funzione qui per vedere quali stanno lavorando
            working_ports = get_working_ports(switches)
            change_link_rate(used_ports,working_ports)
            t_total_energy_required, t_switch_energy = get_instant_energy()
            energy_per_time.append(t_total_energy_required)
            
            info = f"t({count}): {t_total_energy_required} W | working ports: {working_ports}"
            switch_info = ""
            for s, w in t_switch_energy.items():
                switch_info += f"| s{s}: {w} "
                if s not in switch_energy_per_time.keys():
                    switch_energy_per_time[s] = []
                switch_energy_per_time[s].append(w)
            print(info)
            print(switch_info)
            count += 1
            time.sleep(1)
    except KeyboardInterrupt:
        # risultati finali??
        pass

    fig, ax = plt.subplots()
    ax.plot(range(len(energy_per_time)), energy_per_time, color='blue', label='total')
    switch_color = {'1':'steelblue', '2':'orchid', '3':'coral', '4':'gold', '5':'yellowgreen'}
    for s in switch_energy_per_time.keys():
        ax.plot(range(len(switch_energy_per_time[s])), switch_energy_per_time[s], color=switch_color[s], label=f's{s}')
    ax.set(xlabel='time unit', ylabel='Power (W)', title='Power required by all switches in network over time')
    plt.legend(loc="upper left")
    plt.show()