import requests
import pycurl
import json

# curl -X POST -d '{"port_name": "s1-eth3", "max_rate": "10000000000", "queues": [{"max_rate": "1000000000"}]}' http://localhost:8080/qos/queue/0000000000000001

# ===== MODIFICA QUI =====
switch_dpid = '2'
port_no = '2'
rate_mbps = 10000
# ========================

dpid = switch_dpid.rjust(16, '0')
port = f"s{switch_dpid}-eth{port_no}"
rate = str(rate_mbps * 1000 * 1000)

url = f"http://localhost:8080/qos/queue/{dpid}"
#data = '{"port_name": "' + port + '", "max_rate": "10000000000", "queues": [{"max_rate": "' + rate + '"}]}'
#print(data)

crl = pycurl.Curl()

data = json.dumps({"port_name": port , "max_rate": "10000000000", "queues": [{"max_rate": rate }]})

crl.setopt(pycurl.POST, 1)
crl.setopt(crl.URL, url)
crl.setopt(crl.POSTFIELDS, data)
crl.setopt(crl.VERBOSE, 1)

crl.perform()
crl.close()