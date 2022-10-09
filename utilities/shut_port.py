import requests
import pycurl
import json
# config: 1 la shutta, config:0 la rimette up
# se si prova IPERF con PORTA SHUTTATA, ritorna exception ed esce da mininet :(
# curl -X POST -d '{"dpid": 1, "port_no":1, "config": 1, "mask": 1}' http://localhost:8080/stats/portdesc/modify

# ===== MODIFICA QUI =====
switch_dpid = '2'
port_no = '2'
rate_mbps = 0
no_shut = 0
shut = 1
# ========================

dpid = switch_dpid.rjust(16, '0')
port = f"s{switch_dpid}-eth{port_no}"
rate = str(rate_mbps * 1000 * 1000)

url = f"http://localhost:8080/stats/portdesc/modify"
#data = '{"port_name": "' + port + '", "max_rate": "10000000000", "queues": [{"max_rate": "' + rate + '"}]}'
#print(data)

crl = pycurl.Curl()

data = json.dumps({"dpid": switch_dpid, "port_no":port_no, "config": no_shut, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta

crl.setopt(pycurl.POST, 1)
crl.setopt(crl.URL, url)
crl.setopt(crl.POSTFIELDS, data)
crl.setopt(crl.VERBOSE, 1)

crl.perform()
crl.close()