#!/usr/bin/env python

"""
Create a network with 5 hosts, numbered 1-4 and 9.
Validate that the port numbers match to the interface name,
and that the ovs ports match the mininet ports.
"""

from functools import partial
import subprocess
import os
import logging

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info, warn, lg
from mininet.node import OVSKernelSwitch, Node
from mininet.cli import CLI
from mininet.util import quietRun
from mininet.link import TCLink

import time
import sys

flush = sys.stdout.flush

# Create logger
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)

cwd = os.getcwd()




def testBandwidth():

    # Select TCP Reno
    output = quietRun( 'sysctl -w net.ipv4.tcp_congestion_control=reno' )
    #assert 'reno' in output

    subprocess.run([f"{cwd}/start_ryu.sh"])

    net = Mininet( controller=RemoteController, waitConnected=True, switch=OVSKernelSwitch )

    #info( '*** Adding controller\n' )
    c0 = RemoteController("c0", ip="127.0.0.1", port=None)
    net.addController( 'c0' )

    info( '*** Adding hosts\n' )
    server = net.addHost( 'srv', ip='10.0.0.100', dpid="100")
    h1 = net.addHost( 'h1', ip='10.0.0.1', mac='aa:01', dpid="111")
    h2 = net.addHost( 'h2', ip='10.0.0.2', mac='aa:02', dpid="112")
    h3 = net.addHost( 'h3', ip='10.0.0.3', mac='aa:03', dpid="113")
    h4 = net.addHost( 'h4', ip='10.0.0.4', mac='bb:04', dpid="114")
    h5 = net.addHost( 'h5', ip='10.0.0.5', mac='bb:04', dpid="115")
    h6 = net.addHost( 'h6', ip='10.0.0.6', mac='cc:06', dpid="116")
    h7 = net.addHost( 'h7', ip='10.0.0.7', mac='cc:07', dpid="117")

    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1', dpid="1", protocols="OpenFlow13", cls=OVSKernelSwitch, failMode='standalone', stp=True)
    s2 = net.addSwitch( 's2', dpid="2", protocols="OpenFlow13", cls=OVSKernelSwitch, failMode='standalone', stp=True)
    s3 = net.addSwitch( 's3', dpid="3", protocols="OpenFlow13", cls=OVSKernelSwitch, failMode='standalone', stp=True)
    s4 = net.addSwitch( 's4', dpid="4", protocols="OpenFlow13", cls=OVSKernelSwitch, failMode='standalone', stp=True)
    s5 = net.addSwitch( 's5', dpid="5", protocols="OpenFlow13", cls=OVSKernelSwitch, failMode='standalone', stp=True)

    info( '*** Creating links\n' )
    
    net.addLink(s1, s2, port1=1, port2=1)#, cls=TCLink, delay='1ms', bw=1000)
    net.addLink(s1, s3, port1=2, port2=1)#, cls=TCLink, delay='2ms', bw=1000)
    #net.addLink(s1, s4, port1=4, port2=4, cls=TCLink, delay='2ms', bw=1000)
    net.addLink(s2, s4, port1=2, port2=1)#, cls=TCLink, delay='2ms', bw=1000)
    net.addLink(s2, s5, port1=3, port2=1)#, cls=TCLink, delay='2ms', bw=1000)

    net.addLink( server, s1, port2=3)#, cls=TCLink, delay='1ms', bw=1000 )
    net.addLink( h1, s3, port2=2)#, cls=TCLink, delay='10ms', bw=100 )
    net.addLink( h2, s3, port2=3)#,  cls=TCLink, delay='10ms', bw=100 )
    net.addLink( h3, s3, port2=4)#,  cls=TCLink, delay='10ms', bw=100 )
    net.addLink( h4, s4, port2=2)#,  cls=TCLink, delay='10ms', bw=100 )
    net.addLink( h5, s4, port2=3)#,  cls=TCLink, delay='10ms', bw=100 )
    net.addLink( h6, s5, port2=2)#,  cls=TCLink, delay='10ms', bw=100 )
    net.addLink( h7, s5, port2=3)#,  cls=TCLink, delay='10ms', bw=100 )

    #net.addLink(s1, s4, port1=4, port2=4, cls=TCLink, delay='1ms', bw=100)
    ''''''
    net.addLink(s3, s4)
    net.addLink(s1, s4)
    net.addLink(s5, s4)
    net.addLink(s2, s3)
    ''''''
    
    info( '*** Starting network\n' )
    net.build()
    c0.start()
    s1.start( [c0] )
    s2.start( [c0] )
    s3.start( [c0] )
    s4.start( [c0] )
    s5.start( [c0] )
    net.start()

    info(net['s1'].cmd("ovs-vsctl set Bridge s1 protocols=OpenFlow13"))
    info(net['s1'].cmd("ovs-vsctl set-manager ptcp:6632"))
    info(net['s2'].cmd("ovs-vsctl set Bridge s2 protocols=OpenFlow13"))
    info(net['s2'].cmd("ovs-vsctl set-manager ptcp:6632"))
    info(net['s3'].cmd("ovs-vsctl set Bridge s3 protocols=OpenFlow13"))
    info(net['s3'].cmd("ovs-vsctl set-manager ptcp:6632"))
    info(net['s4'].cmd("ovs-vsctl set Bridge s4 protocols=OpenFlow13"))
    info(net['s4'].cmd("ovs-vsctl set-manager ptcp:6632"))
    info(net['s5'].cmd("ovs-vsctl set Bridge s5 protocols=OpenFlow13"))
    info(net['s5'].cmd("ovs-vsctl set-manager ptcp:6632"))

    #while(s1.cmdPrint('ovs-ofctl show s1 | grep -o FORWARD | head -n1') != "FORWARD\r\n"):
    #    time.sleep(3)
    #info( '*** STP ready\n' )

    info(server.cmd("iperf -s -i1 &"))
    info(h1.cmd("iperf -s -i1 &"))
    info(h2.cmd("iperf -s -i1 &"))
    info(h3.cmd("iperf -s -i1 &"))
    info(h4.cmd("iperf -s -i1 &"))
    info(h5.cmd("iperf -s -i1 &"))
    info(h6.cmd("iperf -s -i1 &"))
    info(h7.cmd("iperf -s -i1 &"))
    
    #print(net.linksBetween('s1','s2'))
    CLI(net)
    info( '*** Stopping network\n' )
    net.stop()
    subprocess.run(["mn", "-c"])


if __name__ == '__main__':
    setLogLevel( 'info' )
    testBandwidth()