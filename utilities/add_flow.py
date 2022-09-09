import requests
import pycurl
import json

#

# ===== MODIFICA QUI =====
switch_dpid = '1'
port_in = '1'
port_out = '2'
# ========================


url = f"http://localhost:8080/stats/flowentry/add"

crl = pycurl.Curl()

data = json.dumps({"dpid": switch_dpid, "table_id": 1, "idle_timeout": 300, "match":{"in_port": port_in},"actions":[{"type":"OUTPUT","port":port_out}]})

crl.setopt(pycurl.POST, 1)
crl.setopt(crl.URL, url)
crl.setopt(crl.POSTFIELDS, data)
crl.setopt(crl.VERBOSE, 1)

crl.perform()
crl.close()