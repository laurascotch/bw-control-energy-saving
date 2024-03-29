import pycurl
import json
from io import BytesIO
import time
import re
import matplotlib.pyplot as plt
from bfs_stp import bfs_stp
from initialize_qos import initialize_qos
import sys
import subprocess


# ===== GLOBAL DICTIONARIES =====
#previous_pkt_count = {}     # keeps track of packets in flow, to understand whether there's traffic passing or not
previous_bytes = {}     # keeps track of packets in flow, to understand whether there's traffic passing or not
#prev_port_pkt_count = {}
prev_port_bytes = {}
delta_port_bytes = {}
power_per_intf = {'0.0':0, '10.0':0.1, '100.0':0.2, '1000.0':0.5, '10000.0':5.0}     # link rate (Mbps) : power required (W)
BASE_POWER = 20
used_ports = {}     # keeps track of whether a packet flow is going through a certain port over time

OUTPUT_NAME = "RING_NEAR_"

INITIAL_SPEED = 10
SENSITIVITY = 62500 # bytes per time unit that triggers the sensing of port usage - 1,250,000 is the Bps of 10Mbps, 125000 is the Bps of 1Mbps
ADAPTIVE_BITRATE = True # True per run ottimizzata
DISABLE_UNUSED = True # True per run ottimizzata
MAX_10G = False
ANALYSIS_DURATION = 30

DEBUG_LOG = False

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
            delta_port_bytes[f"{switch_name}-eth{i}"] = [0]

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
                    port_bytes = stats['rx_bytes'] + stats['tx_bytes']
                    prev_port_bytes[port_name] = port_bytes

            #for j in tmp2:
                #previous_pkt_count[f"{switch_name}-{i}-{j}"] = 0
            #    previous_bytes[f"{switch_name}-{i}-{j}"] = 0
    
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
    if DEBUG_LOG:
        print("GET PORTS SPEED")
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
            port_data = ''
            for port in port_names:
                m = re.match("s(\d+)?-eth(\d+)?",port)
                s_id = m[1]
#                port_data = ''
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


def get_working_ports(active_switches,active_ports, ports_speed):
    if DEBUG_LOG:
        print("GET WORKING PORTS")

    working_ports = []
    saturated = []

    for s in active_switches:
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
                port_bytes = stats['rx_bytes'] + stats['tx_bytes']
                delta_bytes = port_bytes - prev_port_bytes[port_name]
                delta_port_bytes[port_name].append(delta_bytes)
                prev_port_bytes[port_name] = port_bytes
                if port_name in active_ports:
                    #if port_bytes > (prev_port_bytes[port_name]+SENSITIVITY):
                    if delta_bytes > (SENSITIVITY * 10):
                        #prev_port_bytes[port_name] = port_bytes
                        working_ports.append(port_name)
                        if delta_bytes > (SENSITIVITY * ports_speed[port_name]):
                            saturated.append(port_name)
    
    return working_ports, saturated


#def change_link_rate(used_ports,working_ports):
def change_link_rate(working_ports, saturated, active_ports, ports_speed):
    if DEBUG_LOG:
        print("CHANGE LINK RATE")
    #ports_speed = get_ports_speed()
    for port in working_ports:
        used_ports[port] += 1

    if DEBUG_LOG:
        print("CHANGE LINK RATE - got used ports")

    urls = []
    data = []
    to_change = 0
    for port in used_ports.keys():
        if port in active_ports:
            #rate_mbps = 10
            rate_mbps = INITIAL_SPEED
            if port in saturated:
                if used_ports[port] > 1 and INITIAL_SPEED<100:
                    rate_mbps = 100
                if used_ports[port] > 3 and INITIAL_SPEED<1000:
                    rate_mbps = 1000
                if used_ports[port] > 6 and MAX_10G:
                    rate_mbps = 10000
            if port not in working_ports:
                used_ports[port] = 0
                #rate_mbps = 10
                rate_mbps = INITIAL_SPEED
                #rate_mbps = 0

            if ports_speed[port] != rate_mbps:
                if DEBUG_LOG:
                    print("CHANGE LINK RATE - changing link rate")
                crl = pycurl.Curl()
                rate = str(rate_mbps * 1000 * 1000)
                dpid = re.match("s(\d+)?-eth\d+",port)[1]
                dpid = dpid.rjust(16, '0')
                url = f"http://localhost:8080/qos/queue/{dpid}"
                d = json.dumps({"port_name": port , "max_rate": "10000000000", "queues": [{"max_rate": rate }]})
                urls.append(url)
                data.append(d)
                to_change += 1
                ports_speed[port] = float(rate_mbps)
                
    # Pre-allocate a list of curl objects
    m = pycurl.CurlMulti()
    m.handles = []
    for i in range(to_change):
        c = pycurl.Curl()
        c.fp = None
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.URL, urls[i])
        c.setopt(pycurl.POSTFIELDS, data[i])
        c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        m.add_handle(c)
    
    while 1:
        ret, num_handles = m.perform()
        if ret != pycurl.E_CALL_MULTI_PERFORM:
            break
    
    # Cleanup
    for c in m.handles:
        if c.fp is not None:
            c.fp.close()
            c.fp = None
        c.close()
    m.close()
    
    return ports_speed
    


def get_instant_energy(ports_speed):
    if DEBUG_LOG:
        print("GET INSTANT ENERGY")
    #ports_speed = get_ports_speed()
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


def compute_switch_throughput(active_switches):
    instant_switch_throughput = {}
    #for s in switches:
    #    instant_switch_throughput[s] = []
    
    for p,dt in delta_port_bytes.items():
        #port_name = f"{switch}-eth{stats['port_no']}"
        m = re.match("s(\d+)?-eth(\d+)?", p)
        s_id = m[1]
        if int(s_id) not in active_switches:
            continue
        if s_id not in instant_switch_throughput.keys():
            instant_switch_throughput[s_id] = dt
        else:
            tmp = instant_switch_throughput[s_id]
            wrap_tmp = [tmp,dt]
            sumindexwise = [sum(x) for x in zip(*wrap_tmp)]
            instant_switch_throughput[s_id] = sumindexwise
    
    for s in instant_switch_throughput.keys():
        tmp = instant_switch_throughput[s]
        mbps = [(x*8/1000000)/2 for x in tmp]   # /2 perché se no conto il throughput doppio perché conto l'ingresso in una porta e l'uscita in un'altra porta (che però è lo stesso traffico)
        instant_switch_throughput[s] = mbps

    if DEBUG_LOG:
        for s,t in instant_switch_throughput.items():
            print(f"{s} = {t}\n===")
    return instant_switch_throughput




def plot_results(energy_per_time, switch_energy_per_time, instant_switch_throughput):

    datafile = open(f"tests/{OUTPUT_NAME}_LOG.txt", "w")
    datafile.write(f"Simulation parameters:\nBase port bitrate: {INITIAL_SPEED} Mbps\nADAPTIVE_BITRATE = {ADAPTIVE_BITRATE}\nDISABLE_UNUSED = {DISABLE_UNUSED}\n10Gbps available = {MAX_10G}\nANALYSIS_DURATION = {ANALYSIS_DURATION}\n===\n")
    
    plt.figure(1)
    plt.hlines(y=sum(energy_per_time)/len(energy_per_time), xmin=0, xmax=len(energy_per_time), color='red', linestyles='--', label='average required power')
    plt.hlines(y=BASE_POWER*len(instant_switch_throughput.keys()), xmin=0, xmax=len(energy_per_time), color='lightcoral', linestyles='--', label='total network base power')
    plt.plot(range(len(energy_per_time)), energy_per_time, color='blue', label='total')
    plt.xlabel("time unit")
    plt.ylabel("Power (W)")
    plt.title("Power required by all switches in network over time")
    plt.ylim(bottom=0, top=max(energy_per_time)*1.1)
    plt.legend(loc="lower left")
    datafile.write(f"AVERAGE POWER = {sum(energy_per_time)/len(energy_per_time)}\n")
    datafile.write(f"ENERGY_PER_TIME = {energy_per_time}\n")
    datafile.write(f"MINIMUM OPERATING POWER = {min(energy_per_time)}\n")
    datafile.write(f"%_TIME_AT_MINIMUM_POWER = {round(energy_per_time.count(min(energy_per_time))/len(energy_per_time)*100)}\n")
    plt.savefig(f"tests/{OUTPUT_NAME}_TOTAL.png")

    plt.figure(2)
    plt.hlines(y=BASE_POWER, xmin=0, xmax=len(energy_per_time), color='r', linestyles='--', label='switch base power')
    switch_color = {'1':'steelblue', '2':'orchid', '3':'coral', '4':'gold', '5':'yellowgreen'}
    for s in switch_energy_per_time.keys():
        plt.plot(range(len(switch_energy_per_time[s])), switch_energy_per_time[s], color=switch_color[s], label=f's{s}')
    plt.xlabel("time unit")
    plt.ylabel("Power (W)")
    plt.title("Power required by each switch in network over time")
    plt.ylim(bottom=0)
    plt.legend(loc="lower right")
    plt.savefig(f"tests/{OUTPUT_NAME}_SWITCH.png")

# instant_switch_throughput è un dizionario '1':[T_t(0), T_t(1), ...], '2' = [...]

    plt.figure(3)
    exchanged_bytes = 0
    avg_switch_throughput = 0
    for s in instant_switch_throughput.keys():
        plt.plot(range(len(instant_switch_throughput[s])), instant_switch_throughput[s], color=switch_color[s], label=f's{s}')
        thr_more_than_zero = len([x for x in instant_switch_throughput[s] if x != 0])
        avg_switch_throughput += ( sum(instant_switch_throughput[s]) / (thr_more_than_zero if thr_more_than_zero>0 else ANALYSIS_DURATION))
        exchanged_bytes += sum(instant_switch_throughput[s])
    plt.xlabel("time unit")
    plt.ylabel("Throughput (Mbps)")
    plt.title(f"Instantaneous throughput of each switch\nAverage throughput per switch: {round((avg_switch_throughput/len(instant_switch_throughput.keys()))/1000, 2)}GB")
    plt.ylim(bottom=0)
    plt.legend(loc="lower right")
    datafile.write(f"AVG_SWITCH_THROUGHPUT = {round((avg_switch_throughput/len(instant_switch_throughput.keys()))/1000, 2)} GB\n")
    plt.savefig(f"tests/{OUTPUT_NAME}_USAGE.png")

    instant_switches_throughput = []
    tmp = []
    for s,l in instant_switch_throughput.items():
        tmp.append(l)
    for i in range(len(tmp[0])):
        t = sum([x[i] for x in tmp])
        if t == 0:
            t = float("NaN")
        else:
            t = t/1000
        instant_switches_throughput.append(t)
    watt_per_gigabyte = [x/y for (x,y) in zip(energy_per_time,instant_switches_throughput)]

    plt.figure(4)
    plt.plot(range(len(watt_per_gigabyte)), watt_per_gigabyte, color='orange', label='total')
    plt.yscale('log')
    plt.xlabel("time unit")
    plt.ylabel("Power (W) per GigaByte (GB)")
    plt.title("Overall Power per GigaByte over time")
    plt.xlim(left=0, right=len(watt_per_gigabyte))
    plt.legend(loc="lower left")
    datafile.write(f"INSTANT_WATT_PER_GB = {watt_per_gigabyte}\n")
    datafile.write(f"AVG_WATT_PER_GB = {(sum(energy_per_time)/len(energy_per_time))/(avg_switch_throughput/1000)}")
    plt.savefig(f"tests/{OUTPUT_NAME}_MEASURE.png")

    plt.draw()
    plt.show()
    datafile.close()



def energy(switches, links, ports_to_hosts, switch_off):
    # set up
    #switches = get_all_switches()
    switched_off = switch_off # contiene str
    active_switches = []
    if DISABLE_UNUSED:
        active_switches = [s for s in switches if str(s) not in switched_off] #active_switches contiene int, switches contiene int
    else:
        active_switches = switches
    switch_ports = get_switch_ports(switches)
    ports = get_all_ports(switches)
    active_links = links
    active_ports = []
    if DISABLE_UNUSED:
        for l,p in active_links.items():
            p = p.split(',')
            active_ports.append(p[0])
        active_ports.extend(ports_to_hosts)
    else:
        active_ports = ports

    # used_ports = {}
    for p in ports:
        used_ports[p] = 0

    count = 0

    # COMMENTAMI SE VUOI GIOCARE COL TRAFFICO
    p = subprocess.Popen([sys.executable, './auto_traffic_emulator.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    energy_per_time = []
    switch_energy_per_time = {}

    #ports_speed = get_ports_speed()

    try:
        while(count <= ANALYSIS_DURATION):
            # TO DO: check if new run of STP is needed
            
            ports_speed = get_ports_speed() # è concettualmente sbagliato averlo qui, ma fuori dal loop non funziona...

            working_ports, saturated = get_working_ports(active_switches,active_ports,ports_speed)
            if ADAPTIVE_BITRATE:
                ports_speed = change_link_rate(working_ports,saturated,active_ports,ports_speed)
            t_total_energy_required, t_switch_energy = get_instant_energy(ports_speed)

            energy_per_time.append(t_total_energy_required + BASE_POWER*len(active_switches))
            
            info = f"working ports: {working_ports}"
            switch_info = ""
            for s, w in t_switch_energy.items():
                if s not in switch_energy_per_time.keys():
                    switch_energy_per_time[s] = []
                if s not in switched_off:
                    switch_info += f"| s{s}: {w+BASE_POWER} "
                    switch_energy_per_time[s].append(w + BASE_POWER)
                else:
                    switch_info += f"| s{s}: {w+0} "
                    switch_energy_per_time[s].append(w + 0)
            print(f" - round {count} : {t_total_energy_required+BASE_POWER*len(active_switches)} W")
            if DEBUG_LOG:
                print(info)
                print(switch_info)
            count += 1
            if not ADAPTIVE_BITRATE:
                time.sleep(3.7)
            time.sleep(0.3)
    except KeyboardInterrupt:
        # non funziona se hai sfiga e interrompi con Ctrl+C mentre è a metà di una richiesta con cURL...
        pass

    instant_switch_throughput = compute_switch_throughput(active_switches)
    plot_results(energy_per_time, switch_energy_per_time, instant_switch_throughput)
    


if __name__ == "__main__":
    # compute BFS STP
    all_links = open("original_links.txt", "w")
    links = get_links()
    for switch_pair,ports in links.items():
        all_links.write(f"{switch_pair}:{ports}\n")
    all_links.close()
    switch_off = []
    links, ports_to_hosts, switch_off, net_graph = bfs_stp()   # links: active links, switch_off: switches that can be completely switched off (because nothing is passing through them)
    print("BREAKING LOOPS in TOPOLOGY")
    # wait for it to install (check_flow tables)
    flows = 0
    while flows<3:
        print(".")
        time.sleep(5)
        flows = check_flows()
    print("NETWORK READY")
    switches = get_all_switches()
    initialize_qos(switches, INITIAL_SPEED)
    print("READY TO RUN ENERGY OPTIMIZATION SCRIPT")
    energy(switches, links, ports_to_hosts, switch_off)