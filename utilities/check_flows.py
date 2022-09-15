import pycurl
import json
from io import BytesIO
import time

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

def check_flows():
    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, 'http://localhost:8080/stats/flow/1')
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.perform()
    crl.close()

    get_body = b_obj.getvalue()
    raw_data = json.loads(get_body.decode('utf8'))
    print(raw_data)
    flows = len(raw_data['1'])

    return flows


if __name__ == "__main__":
    switches = get_all_switches()
    switches.sort()
    flows = 0
    while flows<3:
        time.sleep(2)
        flows = check_flows()
    print("SWITCH READY")