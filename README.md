Carbon Collector
================

A multithreaded implemementation of a (snmp-)data collector for Graphite-Carbon
time series database (https://github.com/graphite-project/carbon). It is rather tiny but efficient snmp-collector 
can easily pull a millons of datasources in a very short period of time (our reference installation
pulls about 300k values via SNMP and pushes those into Graphite-Carbon within 60s every 5 minutes)

The current implementation includes a snmp-poller ([carboncollector/poller.py](carboncollector/poller.py)) class optimised
for Juniper routers. Other vendor's devices may not support all the SNMP-mibs 
that are used. However, the poller can be easily extended or replaced by a
custom implementation and even the included poller will fetch a fair amount of data (primarily interface counters).

For Juniper routers the included SNMP-poller collects the following data:

* Basic Interface Counters (IO-Octets, IO-Packets, IO-Errors/Discards, Unicast/Multicast/Broadcast-Packets)
* Traffic-Class COS (Output-Octets/Packets per Traffic-class, Tail-Drops per class)
* Digital Optical Monitoring (RX/TX Power for single and multilane (40/100G) transceiver)
* JOperating (CPU-utilisation per RE/Linecard, Memory per RE/Linecard)
* Application Process (CPU-utilisation per process, Memory per process)
* MPLS LSP (Bandwidth Utilisation per RSVP LSP, Bandwidth reservation per RSVP LSP)

Using Carbon Collector
--

Carbon collector installs a python module including a command line tool called "ccollector" which reads its configuration 
file from /etc/ccollector/config.py this tool is meant to be executed for each time interval to collect the data and 
write it to Graphite-Carbon. 

The configuration is based on python code itself and basically contains a list of devices and poller methods to execute.
Since python is used for the configuration the configuration can easily pull the list of devices from a external database.
A example configuration can be found in the /examples directory.
 
Requirements
--
Carbon collector depends on the following python packages:

* Python 3.4
* easysnmp
* requests

Installation
--

Download the latest distribution via github releases here:
https://github.com/stoffi92/carbon-collector/releases/latest

pip install downloaded-file.tar.gz
