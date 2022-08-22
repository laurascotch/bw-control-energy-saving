# ==== requests is too slow, especially compared to pycurl ====

#import requests
#
##data = '{"text":"Hello, World!"}'
#
##response = requests.post('http://localhost:8080/qos/queue/all', data=data)
#
#response = requests.get ('http://localhost:8080/qos/queue/all')
#
#raw_data = response.json()
#
#ports_speed = {}
#
#for entry in raw_data:
#    if entry['command_result']['result'] == 'success':
#        switch_ports = entry['command_result']['details']
#        port_names = switch_ports.keys()
#        for port in port_names:
#            speed = switch_ports[port]['0']['config']['max-rate']
#            mbps_speed = int(speed) / (1000 * 1000)
#            ports_speed[port] = mbps_speed
#
#        
#for port, speed in ports_speed.items():
#    print(f"{port}\t\t{speed} Mbps")
#

# ===========================================================

import pycurl
import json
from io import BytesIO

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

        
for port, speed in ports_speed.items():
    print(f"{port}\t\t{speed} Mbps")