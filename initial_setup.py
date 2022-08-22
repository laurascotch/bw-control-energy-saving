import pycurl
import json
from io import BytesIO, StringIO

b_obj = BytesIO()
crl = pycurl.Curl()

crl.setopt(crl.URL, 'http://localhost:8080/stats/switches')
crl.setopt(crl.WRITEDATA, b_obj)

crl.perform()
crl.close()

get_body = b_obj.getvalue()
raw_sw = json.loads(get_body.decode('utf8'))

switches = []

for s in raw_sw:
    dpid = str(s).rjust(16, '0')
    switches.append(dpid)

# prepare switches to use QoS queue system
for dpid in switches:
    data = '"tcp:127.0.0.1:6632"'
    crl = pycurl.Curl()

    url = f"http://localhost:8080/v1.0/conf/switches/{dpid}/ovsdb_addr"
    
    crl.setopt(crl.CUSTOMREQUEST, 'PUT')
    crl.setopt(crl.URL, url)
    crl.setopt(crl.POSTFIELDS, data)
    
    crl.perform()
    crl.close()

# set 10Mbps for all ports of all switches
# curl -X POST -d '{"max_rate": "10000000", "queues": [{"max_rate": "10000000"}]}' http://localhost:8080/qos/queue/0000000000000002
# curl -X POST -d '{"match": {"nw_dst": "0.0.0.0/0"}, "actions":{"queue": "0"}}' http://localhost:8080/qos/rules/0000000000000002
for dpid in switches:
    crl = pycurl.Curl()
    
    url = f"http://localhost:8080/qos/queue/{dpid}"
    data = json.dumps({"max_rate": "10000000", "queues": [{"max_rate": "10000000"}]})
    
    crl.setopt(pycurl.POST, 1)
    crl.setopt(crl.URL, url)
    crl.setopt(crl.POSTFIELDS, data)
    #crl.setopt(crl.VERBOSE, 1)
    
    crl.perform()
    crl.close()

    crl = pycurl.Curl()
    
    url = f"http://localhost:8080/qos/rules/{dpid}"
    data = json.dumps({"match": {"nw_dst": "0.0.0.0/0"}, "actions":{"queue": "0"}})
    
    crl.setopt(pycurl.POST, 1)
    crl.setopt(crl.URL, url)
    crl.setopt(crl.POSTFIELDS, data)
    #crl.setopt(crl.VERBOSE, 1)
    
    crl.perform()
    crl.close()