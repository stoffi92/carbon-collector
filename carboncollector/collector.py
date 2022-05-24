import logging
import pickle
import re
import socket
import struct
import time
from collections import namedtuple
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import queues

log = logging.getLogger(__name__)

WorkItem = namedtuple('WorkItem', 'device poller poller_args methods prefix')
WorkResult = namedtuple('WorkResult', 'num_workitems num_results num_fails')


def escape_carbon(s):
    return re.sub('[^0-9a-zA-Z]+', '_', s)


class CarbonPickleAPI(object):
    def __init__(self, destination):
        pass

    def send(self, data, prefix=None):
        pass


class Collector(object):
    def __init__(self, destination=None, tagsupport=False):
        self.destination = destination
        self.tagsupport = tagsupport

    def _get_socket(self):
        if self.destination:
            _ = self.destination.split(':')
            self.sock = socket.socket()
            try:
                self.sock.connect((_[0], int(_[1])))
            except socket.error:
                raise SystemExit("Couldn't connect to %(server)s on port %(port)d, is carbon-cache.py running?" % {
                    'server': _[0], 'port': int(_[1])})
        else:
            self.sock = None

    def store_data(self, data, prefix=None):
        tuples = ([])
        lines = []
        for item in data:
            _ = []
            if prefix:
                _ = [escape_carbon(a) for a in prefix]
            _.extend([escape_carbon(a) for a in item.path])
            path = '.'.join(_)
            if self.tagsupport and item.tags:
                _ = ['='.join((escape_carbon(k),escape_carbon(v))) for k, v in item.tags.items()]
                # store tagged data with _and_ without tags (this may not be what you want)
                tag_path = path + ';' + ';'.join(_)
                tuples.append((tag_path, (item.timestamp, item.value)))
                lines.append("%s %s %d" % (tag_path, item.value, item.timestamp))
            tuples.append((path, (item.timestamp, item.value)))
            lines.append("%s %s %d" % (path, item.value, item.timestamp))
        message = '\n'.join(lines) + '\n'  # all lines must end in a newline
        if len(tuples):
            log.debug(message)
            package = pickle.dumps(tuples, 1)
            size = struct.pack('!L', len(package))
            if self.sock:
                self.sock.sendall(size)
                self.sock.sendall(package)

    def _worker(self, q, resultq):
        num_workitems = 0
        num_results = 0
        num_fails = 0
        try:
            self._get_socket()
            while 1:
                item = q.get(True, 0.1)
                num_workitems += 1
                log.debug('%s' % str(item))
                start = int(time.time())
                try:
                    p = item.poller(item.device, **item.poller_args)
                    for method in item.methods:
                        result = getattr(p, method)()
                        path = []
                        path.extend(item.prefix)
                        path.append(item.device)
                        num_results += len(result)
                        self.store_data(result, prefix=path)
                except Exception:
                    log.error('Item failed: %s' % str(item), exc_info=True)
                    num_fails += 1
                duration = int(time.time()) - start
                log.debug('%s took: %is' % (str(item), duration))
        except queues.Empty:
            pass
        except Exception:
            log.error('Worker killed by exception', exc_info=True)
        log.debug('Finished worker')
        resultq.put(WorkResult(num_workitems=num_workitems, num_results=num_results, num_fails=num_fails))

    def collect(self, items, num_threads=1):
        q = Queue()
        resultq = Queue()
        for item in items:
            q.put(item)
        processes = []
        for i in range(num_threads):
            p = Process(target=self._worker, args=(q, resultq))
            p.start()
            processes.append(p)
        for process in processes:
            process.join()
        resultq.put(None)
        num_workitems = 0
        num_results = 0
        num_fails = 0
        for i, result in enumerate(iter(resultq.get, None)):
            num_workitems += result.num_workitems
            num_results += result.num_results
            num_fails += result.num_fails
            log.info('%i num_workitems: %s, num_results: %s, num_fails: %s' %(i, result.num_workitems, result.num_results, result.num_fails))
        log.info('TOTALS: num_workitems: %s, num_results: %s, num_fails: %s' %(num_workitems, num_results, num_fails))
