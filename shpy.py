py time.sleep(4)
py net['srv'].cmd("iperf -c 10.0.0.7 -n 2000M -i2 &")
py time.sleep(7)
py net['h6'].cmd("iperf -c 10.0.0.100 -n 1500M -i2 &")
py time.sleep(1)
py time.sleep(8)
py time.sleep(1)
py time.sleep(4)
py net['h5'].cmd("iperf -c 10.0.0.100 -n 800M -i2 &")
py time.sleep(17)
py net['srv'].cmd("iperf -c 10.0.0.6 -n 2500M -i2 &")
py time.sleep(5)
py net['srv'].cmd("iperf -c 10.0.0.5 -n 1500M -i2 &")
py time.sleep(20)
py net['h6'].cmd("iperf -c 10.0.0.100 -n 800M -i2 &")
py time.sleep(3)
py net['h5'].cmd("iperf -c 10.0.0.100 -n 250M -i2 &")
py time.sleep(1)