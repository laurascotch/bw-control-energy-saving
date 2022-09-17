import pycurl
import json
from io import BytesIO, StringIO

def initialize_qos(switches):
    for s in switches:
        dpid = str(s).rjust(16, '0')
        data = '"tcp:127.0.0.1:6632"'
        crl = pycurl.Curl()

        url = f"http://localhost:8080/v1.0/conf/switches/{dpid}/ovsdb_addr"

        crl.setopt(crl.CUSTOMREQUEST, 'PUT')
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)

        crl.perform()
        crl.close()

    for s in switches:
        dpid = str(s).rjust(16, '0')
        crl = pycurl.Curl()
    
        url = f"http://localhost:8080/qos/queue/{dpid}"
        data = json.dumps({"max_rate": "10000000", "queues": [{"max_rate": "10000000"}]})

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)

        crl.perform()
        crl.close()

    for s in switches:
        dpid = str(s).rjust(16, '0')
        crl = pycurl.Curl()

        url = f"http://localhost:8080/qos/rules/{dpid}"
        data = json.dumps({"match": {"nw_dst": "0.0.0.0/0"}, "actions":{"queue": "0"}})

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)

        crl.perform()
        crl.close()