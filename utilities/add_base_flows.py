import requests
import pycurl
import json

#

# ===== MODIFICA QUI =====
switch_dpid = '1'
port_in = 1
port_out = 2
# ========================

data0 = json.dumps({"dpid": switch_dpid, "priority": 65535, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": ["OUTPUT:CONTROLLER"], "match": {"dl_type": 35020}, "table_id": 0})
data1 = json.dumps({"dpid": switch_dpid, "priority": 0, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": ["GOTO_TABLE:1"], "match": {}, "table_id": 0})
data2 = json.dumps({"dpid": switch_dpid, "priority": 0, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": ["OUTPUT:CONTROLLER"], "match": {}, "table_id": 1})

url = f"http://localhost:8080/stats/flowentry/add"

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

crl = pycurl.Curl()

crl.setopt(pycurl.POST, 1)
crl.setopt(crl.URL, url)
crl.setopt(crl.POSTFIELDS, data2)
crl.setopt(crl.VERBOSE, 1)

crl.perform()
crl.close()