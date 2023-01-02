import pycurl
import json
from io import BytesIO


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
        switches.append(str(s))

    return switches


def clean_flows(switches):
    for switch_dpid in switches:
        url = f"http://localhost:8080/stats/flowentry/delete"

        crl = pycurl.Curl()

        #data = json.dumps({"dpid": switch_dpid, "table_id": 1, "match":{"in_port": port_in},"actions":[{"type":"OUTPUT","port":port_out}]})
        data = json.dumps({"dpid": switch_dpid, "table_id": 1})

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()

        data0 = json.dumps({"dpid": switch_dpid, "priority": 65535, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": ["OUTPUT:CONTROLLER"], "match": {"dl_type": 35020}, "table_id": 0})
        data1 = json.dumps({"dpid": switch_dpid, "priority": 0, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": ["GOTO_TABLE:1"], "match": {}, "table_id": 0})
        data2 = json.dumps({"dpid": switch_dpid, "priority": 0, "cookie": 0, "idle_timeout": 0, "hard_timeout": 0, "flags": 0, "actions": [{"type":"OUTPUT","port":"CONTROLLER"}], "match": {}, "table_id": 1})
        
        url = f"http://localhost:8080/stats/flowentry/add"
        ''''''
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
        ''''''
        crl = pycurl.Curl()
        
        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data2)
        crl.setopt(crl.VERBOSE, 1)
        
        crl.perform()
        crl.close()


if __name__ == "__main__":
    switches = get_all_switches()
    switches.sort()
    clean_flows(switches)