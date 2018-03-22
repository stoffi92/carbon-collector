import re
import subprocess
import time
from collections import OrderedDict

from easysnmp import Session
from collections import namedtuple

QueryRecord = namedtuple('QueryRecord', 'path value timestamp tags')

import logging
log = logging.getLogger(__name__)

def filter_nonprintable(text):
    import string
    # Get the difference of all ASCII characters from the set of printable characters
    nonprintable = set([chr(i) for i in range(128)]).difference(string.printable)
    # Use translate to remove all non-printable characters
    return text.translate({ord(character):None for character in nonprintable})


class SnmpPoller(object):
    JUNIPER_GRAPH_APPLICATIONS = ['/usr/sbin/rpd', '/usr/sbin/sfid']

    def __init__(self, hostname, community='public', version=2, jgraph_applications=JUNIPER_GRAPH_APPLICATIONS):
        self.hostname = hostname.lower()
        self.session = Session(hostname=self.hostname, community=community, version=version, use_numeric=True)
        self.ifmap = OrderedDict()
        self.ifaliases = OrderedDict()
        self.iftags = OrderedDict()
        self.init_ifmap()
        self.jgraph_applications = jgraph_applications

    def _bulkwalk(self, oids):
        results = OrderedDict()
        for mib, oid in oids.items():
            results[mib] = self.session.bulkwalk(oid)
        return results

    def init_ifmap(self):
        # index = OrderedDict()
        _ = self.session.bulkwalk('1.3.6.1.2.1.31.1.1.1.1', max_repetitions=2) # ifdesc
        for item in _:
            self.ifmap[item.oid_index] = str(item.value)
        # aliases = OrderedDict()
        _ = self.session.bulkwalk('1.3.6.1.2.1.31.1.1.1.18', max_repetitions=2) # ifalias
        for item in _:
            self.ifaliases[item.oid_index] = str(item.value)
            m = re.search(r'\$([^\$].*)\$', str(item.value))
            if m:
                tags = [a.strip() for a in m.group(1).split(',')]
                for tag in tags:
                    try:
                        k, v = tag.split('=', 2)
                        l = self.iftags.get(item.oid_index, {})
                        l[k.strip()] = v.strip()
                        self.iftags[item.oid_index] = l
                    except Exception:
                        log.error('host: %s invalid tag syntax found in ifalias: %s' %(self.hostname, tag))

    def lookup_iftags(self, if_idx):
        return self.iftags.get(if_idx, None)

    def ifalias_query(self):
        # 'ifAlias': '1.3.6.1.2.1.31.1.1.1.18', <- spaeter ein query dafür machen?
        # results = self.session.bulkwalk('1.3.6.1.2.1.31.1.1.1.18')
        output = []
        now = int(time.time())
        for k, v in self.ifmap.items():
            _ = QueryRecord(path=('iface', v), value=self.ifaliases.get(k, ''),
                            timestamp=now, tags=self.lookup_iftags(k))
            output.append(_)
        return output

    def iftable_query(self):
        mib_if_tables = {
           'ifHCOutOctets': '1.3.6.1.2.1.31.1.1.1.10',
            'ifHCOutUcastPkts': '1.3.6.1.2.1.31.1.1.1.11',
            'ifHCOutMulticastPkts': '1.3.6.1.2.1.31.1.1.1.12',
            'ifHCOutBroadcastPkts': '1.3.6.1.2.1.31.1.1.1.13',
            'ifHighSpeed': '1.3.6.1.2.1.31.1.1.1.15',
            'ifInMulticastPkts': '1.3.6.1.2.1.31.1.1.1.2',
            'ifInBroadcastPkts': '1.3.6.1.2.1.31.1.1.1.3',
            'ifOutMulticastPkts': '1.3.6.1.2.1.31.1.1.1.4',
            'ifOutBroadcastPkts': '1.3.6.1.2.1.31.1.1.1.5',
            'ifHCInOctets': '1.3.6.1.2.1.31.1.1.1.6',
            'ifHCInUcastPkts': '1.3.6.1.2.1.31.1.1.1.7',
            'ifHCInMulticastPkts': '1.3.6.1.2.1.31.1.1.1.8',
            'ifHCInBroadcastPkts': '1.3.6.1.2.1.31.1.1.1.9',
            'ifInDiscards': '1.3.6.1.2.1.2.2.1.13',
            'ifOutDiscards': '1.3.6.1.2.1.2.2.1.19',
            'ifInErrors': '1.3.6.1.2.1.2.2.1.14',
            'ifOutErrors': '1.3.6.1.2.1.2.2.1.20',
        }
        results = self._bulkwalk(mib_if_tables)
        output = []
        now = int(time.time())
        for k, items in results.items():
            for item in items:
                _ = QueryRecord(path=('iface', self.ifmap[item.oid_index], k), value=item.value,
                                           timestamp=now, tags=self.lookup_iftags(item.oid_index))
                output.append(_)
        return output

    def location_query(self):
        result = self.session.get('1.3.6.1.2.1.1.6')
        now = int(time.time())
        return [QueryRecord(path=(), value=result.value, timestamp=now, tags=None)]

    def jnx_transceiver_query(self):
        mib_dom_tables = {
            'jnxDomCurrentLaneRxLaserPower': '1.3.6.1.4.1.2636.3.60.1.2.1.1.6',
            'jnxDomCurrentLaneTxLaserOutputPower': '1.3.6.1.4.1.2636.3.60.1.2.1.1.8',
            'jnxDomCurrentLaneLaserTemperature': '1.3.6.1.4.1.2636.3.60.1.2.1.1.9',
        }
        # TODO: module voltage and module temperature / maybe remove lanetemperature
        mib_dom_tables2 = {
            'jnxDomCurrentModuleTemperature': '1.3.6.1.4.1.2636.3.60.1.1.1.1.8',
        }
        results = self._bulkwalk(mib_dom_tables)
        output = []
        now = int(time.time())
        for k, items in results.items():
            for item in items:
                ifoid = item.oid.split('.')[-1]
                _ = QueryRecord(path=('iface', self.ifmap[ifoid], 'dom', k, 'lane%s' % item.oid_index),
                                           value=item.value, timestamp=now, tags=self.lookup_iftags(item.oid_index))
                output.append(_)
        return output

    def jnx_operating_query(self):
        """
            TODO:
             jnxHrStoragePercentUsed.1
            Monitors the /dev/ad0s1a: file system on the switch. This is the root file system mounted on /.
            jnxHrStoragePercentUsed.2
            Monitors the /dev/ad0s1e: file system on the switch. This is the configuration file system mounted on /config.
        """
        # applications = ['/usr/sbin/rpd', 'usr/sbin/sfid']

        mib_joperating_tables = {
            'jnxFruType': '1.3.6.1.4.1.2636.3.1.15.1.6',  # hier die mit 6 und 3 suchen (RE, FPC)
            'jnxFruName': '1.3.6.1.4.1.2636.3.1.15.1.5',
            'sysApplElmtRunName': '1.3.6.1.2.1.54.1.2.3.1.7',  # prozesses suchen sfid, rpd
        }
        mib_fru = {
            'CPU': '1.3.6.1.4.1.2636.3.1.13.1.21', #5min avg cpu
            #'CPU': '1.3.6.1.4.1.2636.3.1.13.1.8', #peak cpu?
            'Temp': '1.3.6.1.4.1.2636.3.1.13.1.7',
            'usedMemory': '1.3.6.1.4.1.2636.3.1.13.1.15',
            'usedMemoryPercent': '1.3.6.1.4.1.2636.3.1.13.1.11',  # memory util in percent
        }

        mib_appl = {
            'CPU': '1.3.6.1.2.1.54.1.2.3.1.9',
            'usedMemory': '1.3.6.1.2.1.54.1.2.3.1.10',
        }

        results = self.session.bulkwalk(mib_joperating_tables['jnxFruType'])
        fpcre_oids = OrderedDict()

        for result in results:
            if result.value in ('6', '3'):
                id = result.oid[len(mib_joperating_tables['jnxFruType'])+1:] + '.0'
                fpcre_oids[id] = mib_joperating_tables['jnxFruName'] + id
        names = self.session.get(list(fpcre_oids.values()))
        names = [a.value for a in names]
        oid_2_names = dict(zip(fpcre_oids.keys(), names))
        requesttable = []
        for mibname, miboid in mib_fru.items():
            for oid, name in oid_2_names.items():
                requesttable.append(QueryRecord(path=('hw', name, mibname),
                                                           value= miboid + oid, timestamp=None, tags=None))

        requests = [a.value for a in requesttable]
        responses = self.session.get(requests)
        output = []
        now = int(time.time())
        for request, response in zip(requesttable,responses):
            if response.snmp_type != 'NOSUCHINSTANCE':
                output.append(QueryRecord(path=request.path, value=response.value, timestamp=now, tags=None))
        # appl-mib
        results = self.session.bulkwalk(mib_joperating_tables['sysApplElmtRunName'])

        requesttable = []
        for result in results:
            if result.value in self.jgraph_applications:
                for name, oid in mib_appl.items():
                    id = result.oid[len(mib_joperating_tables['sysApplElmtRunName']) + 1:] + '.' + result.oid_index
                    requesttable.append(QueryRecord(path=('appl', result.value, name),
                                                               value=oid + id, timestamp=None, tags=None))
        requests = [a.value for a in requesttable]
        responses = self.session.get(requests)
        for request, response in zip(requesttable,responses):
            if response.snmp_type != 'NOSUCHINSTANCE':
                output.append(QueryRecord(path=request.path, value=response.value, timestamp=now, tags=None))
        return output

    def jnx_lsp_query(self):
        mib_lsp_tables = {
            'mplsLspInfoName': '1.3.6.1.4.1.2636.3.2.5.1.1',
            'mplsLspOctets': '1.3.6.1.4.1.2636.3.2.5.1.3',
            'mplsLspPackets': '1.3.6.1.4.1.2636.3.2.5.1.4',
            'mplsLspBandwidth': '1.3.6.1.4.1.2636.3.2.5.1.21',
        }
        results = self._bulkwalk(mib_lsp_tables)
        lsp_name_table = {}
        lsp_names = results.pop('mplsLspInfoName')
        for name in lsp_names:
            lsp_name = filter_nonprintable(name.value)
            oid = name.oid[len(mib_lsp_tables['mplsLspInfoName']) + 1:] + '.' + name.oid_index
            lsp_name_table[oid] = lsp_name
        output = []
        now = int(time.time())
        for k, v in results.items():
            for item in v:
                name_id = item.oid[len(mib_lsp_tables[k]) + 1:] + '.' + item.oid_index
                _ = QueryRecord(path=('lsp', lsp_name_table[name_id], k), value=item.value, timestamp=now, tags=None)
                output.append(_)
        return output

    def jnx_cos_query(self):
        mib_cos_tables = {
            'IfqTxedBytes':	'1.3.6.1.4.1.2636.3.15.1.1.9',
            'IfqTxedPkts':	'1.3.6.1.4.1.2636.3.15.1.1.7',
            'IfqTailDropPkts': '1.3.6.1.4.1.2636.3.15.1.1.11',
        }
        results = self._bulkwalk(mib_cos_tables)
        output = []
        now = int(time.time())
        for k, v in results.items():
            for item in v:
                oid = item.oid[len(mib_cos_tables[k]) + 2:] + '.' + item.oid_index
                _ = oid.split('.')
                ifidx = _[0]
                fcname = ''.join(list((chr(int(c)) for c in _[2:])))
                ifname = self.ifmap[ifidx]
                _ = QueryRecord(path=('iface', ifname, 'cos', fcname, k), value=item.value, timestamp=now,
                            tags = self.lookup_iftags(ifidx))
                output.append(_)
        return output

    def jnx_all(self):
        output = []
        try:
            output.extend(self.iftable_query())
            output.extend(self.jnx_transceiver_query())
            output.extend(self.jnx_operating_query())
            output.extend(self.jnx_lsp_query())
            output.extend(self.jnx_cos_query())
        except Exception:
            log.error('SnmpPoller failed for %s' % self.hostname, exc_info=True)
        return output

    def cisco_all(self):
        output = self.iftable_query()
        return output


def subprocessrun(l):
    proc = subprocess.Popen(l,stdout=subprocess.PIPE)
    lines = []
    for line in proc.stdout:
        lines.append(line.decode().strip())
    return lines


class UtilityPoller(object):
    def __init__(self, hostname):
        self.hostname = hostname.lower()

    def ping(self):
        lines = subprocessrun(["ping", self.hostname, "-c", "10", "-i", "0.3", "-q"])
        result = []
        for line in lines:
            _ = re.match(r'.*\s+([0-9|.]+)% packet loss\s*', line)
            if _:
                loss = _.group(1)
                loss = float(loss)
                if loss != 0:
                    now = int(time.time())
                    result.append(QueryRecord(path=('ping', 'loss',), value=str(loss), timestamp=now, tags=None))
                continue
            _ = re.match(r'.*=\s+([0-9|.]+)/([0-9|.]+)/([0-9|.]+)/[0-9|.]+\s+.*', line)
            if _:
                min, avg, max = _.group(1), _.group(2), _.group(3)
                now = int(time.time())
                result.append(QueryRecord(path=('ping', 'min',), value=min, timestamp=now, tags=None))
                result.append(QueryRecord(path=('ping', 'avg',), value=avg, timestamp=now, tags=None))
                result.append(QueryRecord(path=('ping', 'max',), value=max, timestamp=now, tags=None))
                break
        return result
