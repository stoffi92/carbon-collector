Carbon Collector
================

A multithreaded implemementation of a (snmp-)data collector for Graphite-Carbon
time series database (https://github.com/graphite-project/carbon). It is rather tiny but efficient snmp-collector 
can easily pull a millons of datasources in a very short period of time (our reference installation
pulls about 300k values via SNMP and pushes those into Graphite-Carbon within 60s every 5 minutes)
