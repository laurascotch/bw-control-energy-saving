# How to run this project

### Get the latest version of the testbed ComNetsEmu
In fact, installing Mininet and Ryu would be enough, but [ComNetsEmu](https://git.comnets.net/public-repo/comnetsemu) comes with everything we need already available for use.

Just follow the instruction on both [this page](https://stevelorenz.github.io/comnetsemu/installation.html) and the original repo page for the installation. For this project, I choose to use the pre-built VM image for VirtualBox. 

### Clone this repository and setup a VirtualBox shared folder
Setup a VirtualBox shared folder between the ComNetsEmu VM and the repo directory in your host system. This will allow for easy copy-pasting of files.

For reference, the shared directory in "my" VM is located at `/home/vagrant/bw-control-energy-saving`.

### Place all the needed files in the right directory
From the shared folder, copy `mesh.py`, `utilities/qos_simple_switch_13.py`, `start_ryu.sh` and `shpy.py` in `/home/vagrant/comnetsemu`:

`cd ~/bw-control-energy-saving`
`cp mesh.py ~/comnetsemu`
`cp qos_simple_switch_13.py ~/comnetsemu`
`cp start_ryu.py ~/comnetsemu`
`cp shpy.py ~/comnetsemu`

Make sure that `start_ryu.sh` is executable.

### You are now ready to run the project
#### Initial setup
| Where | What to do |
|---|---|
| VM | Run the network simulation (whatever topology you want)<br>`cd ~/comnetsemu`<br>`sudo python3 mesh.py`<br>Wait for the mininet shell to appear |
| Host | In a browser, check that `http://localhost:8080/stats/switches` returns a list of 5 switches |
| Host | In a browser, check that `http://localhost:8080` shows the topology |
| Host | Run `python3 run_project.py` |

#### The Digital Twin for energy optimization is now running

The switches' power consuption is shown in the terminal in real-time.

`run_project.py` will automatically run also the traffic generation script inside mininet. If you don't want this to happen, just comment out line 524 (`p = subprocess.Popen([sys.executable, './auto_traffic_emulator.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)`).

Did you chose to generate traffic yourself? *Let's play with our network!*

You didn't? Skip to next paragraph...

Let's go back to the VM.

The 7 hosts plus 1 server available in the network defined in `mesh.py` are set up to act as iperf clients.

Wanna test how the network behaves when the server `srv` transmits 2GB of data to the host `h7` (10.0.0.7)? Let's emulate it in mininet:
`srv iperf -c 10.0.0.7 -n 1000M -i2` (use `srv iperf -c 10.0.0.7 -n 1000M -i2 &` execute in the backgroud)
 - `-c [a.b.c.d]` is the destination address
 - `-n [xxx][K|M]` is the size of the data in KyloBytes or MegaBytes
 - `-i[n]` is the interval to print statistics of the test. `-i2` is an interval of two seconds, `-i1` is one second

In the terminal where `run_project.py` is running, you should notice that quite a few interfaces are working and that the power usage of some switches has changed. 
In the meanwhile, in the iperf statistics shown in the mininet CLI, you should notice the connection speed increasing to allow the transmission to finish in as few seconds as possible.

#### Changing topology
Upon activating/deactivating links, you need to recalculate the spanning tree of the network in order to break unwanted loops.

| Where | What to do |
|---|---|
| Host | Check the topology at `http://localhost:8080` |
| Host | Run `python3 utilities/get_graph.py` which will break the loops in the topology |
| Host | Wait up to 2 minutes. By refreshing the web page of the topology, you should see it changing |
| Host | Clear the flow table of all the switches by running: `python3 utilities/clean_flows.py` |
| VM | Try a `pingall` in the mininet shell |
| Host | In a browser, check that `http://localhost:8080/stats/flow/<switch_id>` shows a populated flow table |

### End of the experiment

You are now satisfied and you want to have a look on how the network behaved in terms of power consumption: stop the `run_project.py` script with `[Ctrl] + C`. This will return a plot showing the power consumption over time.

Switch to the VM, where you can stop the network by typing `exit` in the mininet CLI.