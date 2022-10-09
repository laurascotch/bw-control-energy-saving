import pycurl
import json
import sys
import re
# config: 1 la shutta, config:0 la rimette up
# se si prova IPERF con PORTA SHUTTATA, ritorna exception ed esce da mininet :(
# curl -X POST -d '{"dpid": 1, "port_no":1, "config": 1, "mask": 1}' http://localhost:8080/stats/portdesc/modify

if __name__ == "__main__":

    link_shut = {}
    if len(sys.argv) < 3:
        print("USAGE: link_status.py sX,sY up sA,sB down <link> <up|down> ...")
        exit()
    else:
        del sys.argv[0]
        if len(sys.argv)%2 != 0:
            print("USAGE: link_status.py sXsY up sAsB down <link> <up|down> ...")
            exit()
        else:
            for i in range(0,len(sys.argv),2):
                l = sys.argv[i]
                s = sys.argv[i+1]
                if s == 'up':
                    link_shut[l] = 0
                elif s == 'down':
                    link_shut[l] = 1
                else:
                    print("USAGE: link_status.py sXsY up sAsB down <link> <up|down> ...")
                    exit()

    link_file = open("original_links.txt", "r")
    lines = link_file.readlines()
    links = {}
    for l in lines:
        l = l.strip('\n')
        l = l.split(':')
        if len(l) == 2:
            links[l[0]] = l[1]

    for l,s in link_shut.items():
        ports = links[l]
        ports = ports.split(',')
        m1 = re.match("s(\d+)?-eth(\d+)?", ports[0])
        s1 = m1[1]
        p1 = m1[2]
        m2 = re.match("s(\d+)?-eth(\d+)?", ports[1])
        s2 = m2[1]
        p2 = m2[2]

        status = s

        url = f"http://localhost:8080/stats/portdesc/modify"
        crl = pycurl.Curl()

        data = json.dumps({"dpid": s1, "port_no":p1, "config": status, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()

        crl = pycurl.Curl()

        data = json.dumps({"dpid": s2, "port_no":p2, "config": status, "mask": 101})   # mask 101 per non avere problemi. config 1 shutta, config 0 unshutta

        crl.setopt(pycurl.POST, 1)
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, data)
        crl.setopt(crl.VERBOSE, 1)

        crl.perform()
        crl.close()
