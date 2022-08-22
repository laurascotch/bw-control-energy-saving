# Bandwidth control for energy saving

This project is the subject of the final dissertation for the MSc Degree in Computer Science at University of Trento, Italy. 

The goal is to implement and run the digital twin of a network in order to optimize its energy usage.


### What is a Digital Twin?
A digital twin is a real-time simulation of a real-world system (physical twin). The digital twin serves as a counterpart of the real twin and allows for monitoring of the latter, as well as forecasting future scenarios and validating the best options to best react to them.

Digital Twins are used in a large number of areas, from the aerospace industry to economics. This project focuses on a possible use in the telecommunications field.

One of the biggest challenges when developing a Digital Twin is dealing with the huge amount of data a system can generate. It is important to clearly define what the goal is, so that the effort is focused only on the needed data: bigger quantities require bigger resources to allow for real-time gathering and analysis.


### A bit of context - Energy consuption of a network device
What follows is a summary of the main concepts expressed in [Analyzing Local Strategies for Energy-Efficient Networking](https://doi.org/10.1007/978-3-642-23041-7_28).

The tendency towards miniaturization and the ICT growing dynamic aren't effectively aiming at reducing power consumption. In particular, miniaturization has reduced the single unit power consumption, but it allows for more ports to be put into the same device, thus increasing performances and power utilization (rebound effect, Jevons paradox). The result is that the total power required per node in a network is growing.

Experimental measurements ([Ref1](https://ieeexplore.ieee.org/abstract/document/4509688)) from many different network devices show that half of the energy consumption is due to the base system, while the other half depends on the number of installed line interface cards (even if idle). Furthermore, the power consumption of routers and switches is, quite surprisingly, independent from the network load, resulting in a difference of just 3% more energy required by heavy loaded network devices, compared to idle ones. This is a clear suggestion that it is crucial to develop energy-efficient architectures able to temporarily switch off entire devices or at least some parts, so to minimize energy consumption as much as possible.

Putting in sleep mode entire nodes may be unpractical for various reasons, mainly: a) it is unconvenient, investment-wise, to switch off highly expensive transmission links; b) decreasing the meshing degree of a network leads to lesser reliability and difficulty in load balancing.

Putting in sleep mode only single interfaces of a device may be really effective in terms of energy saving, in particular when operating at high speed: in a common commercial Ethernet switch Catalyst 2970 24-ports LAN switch) a 1000baseT adds 1.8 W to the overall energy consumption. The following table gives an insight of interface power consumption of the vast majority of commercial off-the-shelf network devices.

| Active interfaces | 10BaseT | 100BaseT | 1000BaseT |
|---|---|---|---|
| 0 | 69.1 | 69.1 | 69.1 |
| 2 | 70.2 | 70.1 | 72.9 |
| 4 | 71.1 | 70.0 | 76.7 |
| 6 | 71.6 | 71.1 | 80.2 |
| 8 | 71.9 | 71.9 | 83.7 |

There are two main per-interface sleeping mechanisms, ALR and LPI. ALR is based on the ability of dinamically modifying the link rate according to the traffic needs: in fact, operating devices at lower frequency can enable energy consumption reduction. In LPI, transmission on a single interface is stopped when there's no data to send and quickly resumed when new packets arrive, instead of having the continuous IDLE signal typical of legacy systems. 

It is important to remember that in network environments where packet arrival rates can be highly non-uniform, allowing interface transitions between different operating rates or sleep/active modes can introduce additional delays or even losses.

In order to provide realistic values regarding the energy consuption during the simulation, the following table is considered. The table shows the energy/power consumption of interfaces working at their native link rates for most commercial off-the-shelf network devices.

| Native link rate | Power per interface | Energy Scaling Index | Energy Consumption Rate (power per Gbps) |
|---|---|---|---|
| 10 Mbps | 0.1 W | 10 nJ/bit | 10 W/Gbps |
| 100 Mbps | 0.2 W | 2 nJ/bit | 2 W/Gbps |
| 1000 Mbps | 0.5 W | 0.5 nJ/bit | 0.5 W/Gbps |
| 10000 Mbps | 5.0 W | 0.5 nJ/bit | 0.5 W/Gbps |

We can notice that the energy consumption for forwarding one bit isn't the same for every interface, but depends on its native link rate.

Observations confirm that an interface consumes the same power whatever its current throughput is: power consumption is throughput independent. It derives that the link rate can be adapted to the current throughput (by using ALR) with consequent energy savings.


### Project outline
As it is beyond my possibilities to run this project on a real network, the whole architecture is emulated by using the renowned [Mininet](http://mininet.org/) network emulator.

The Ryu controller allows to gather data from the network via OpenFlow messages that report different events, such as packet flows through devices' interfaces, ports' working parameters, etc.

Ryu also allows to perform actions that modify the behavior of the network. The action to be taken is determined by an algorithm which is the core of this project.
