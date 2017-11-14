from carboncollector import WorkItem
from carboncollector import SnmpPoller
from carboncollector import UtilityPoller


# Carbon pickle interface that should be used by the collector instances to write the data to the database
carbon_pickle = '127.0.0.1:2004'

# Number of processes (this is actually a number of processes *not* threads!)
num_threads = 8

# Poller workitems that the collector should execute
items = []

devices = ('test1.example.com',
           'test2.example.com',
           'test3.example.com',
           )

for d in devices:
    # included juniper SNMP Poller
    # See other possible "methods" in the poller-source code
    items.append(WorkItem(device=d, poller=SnmpPoller, methods=['jnx_all',], poller_args={'community': 'private'}),
                 prefix=('optional_prefix', ))
    # included Ping-Statistics (minimal smokeping-stats-replacement)
    items.append(WorkItem(device=d, poller=UtilityPoller, methods=['ping'],
                     poller_args={}, prefix=('nl',)))
