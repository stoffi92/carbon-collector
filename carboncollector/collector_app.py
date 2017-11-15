import sys
import logging
import argparse
from logging import StreamHandler
from .collector import Collector

CFGPATH = '/etc/ccollector/'

def main():
    # enable logging to terminal for the module
    ccl = logging.getLogger('carboncollector')
    sh = StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(fmt='%(asctime)-15s %(name)-5s %(levelname)s %(message)s'))
    ccl.addHandler(sh)
    ccl.setLevel(logging.INFO)

    # command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', required=False, metavar='cfgpath',
                        help='Path where the configuration file config.py can be found.',
                        default=CFGPATH)
    args = parser.parse_args()
    sys.path.append(args.p)

    # configuration
    import config as cfg
    tagsupport = getattr(cfg, 'tagsupport', False)
    collector_class = getattr(cfg, 'collector_class', Collector)
    collector_args = getattr(cfg, 'collector_args', {})

    c = collector_class(**collector_args)
    c.collect(cfg.items, num_threads=getattr(cfg, 'num_threads', 1))


if __name__ == '__main__':
    main()
