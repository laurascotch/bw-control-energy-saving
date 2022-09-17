#!/bin/bash

# Start ryu controller application
printf '*** Starting RYU Controller on localhost ***\n'

#ryu-manager ryu.app.simple_switch_stp_13 ryu.app.rest_conf_switch ryu.app.gui_topology.gui_topology --observe-links &> /home/shared/stp_logs.txt &
ryu-manager ryu.app.rest_qos qos_simple_switch_13.py ryu.app.rest_conf_switch ryu.app.gui_topology.gui_topology --observe-links &> /home/shared/ryu-logs.log &
#ryu-manager multipath.py ryu.app.ofctl_rest ryu.app.rest_conf_switch --observe-links &> /home/shared/multipath/ryu-logs.log &

sleep 10
