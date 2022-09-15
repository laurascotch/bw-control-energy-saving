#!/bin/bash

# Start ryu controller application
printf '*** Starting RYU Controller on localhost ***\n'

#ryu-manager ryu.app.simple_switch_stp_13 ryu.app.gui_topology.gui_topology --observe-links &> ryu-logs.log &
ryu-manager ryu.app.rest_qos qos_simple_switch_13.py ryu.app.ofctl_rest ryu.app.rest_conf_switch ryu.app.gui_topology.gui_topology --observe-links &> /home/shared/ryu-logs.log &
#ryu-manager ryu.app.simple_switch_13 ryu.app.ofctl_rest ryu.app.rest_topology ryu.app.rest_qos --observe-links &> /home/shared/ryu-logs.log &
#ryu-manager ~/flowmanager/flowmanager.py ~/OF-BW-Control/Rest.py ryu.app.ofctl_rest ryu.app.rest_topology --observe-links &> /home/shared/ryu-logs.log &
#ryu-manager ~/OF-BW-Control/Rest.py &> of-bw-logs.log &
sleep 10
