import logging
from logging import StreamHandler
import sys
import argparse
from .tagcollector import TagCollector

CFGPATH = '/etc/ccollector/'


def main():
    # enable logging to terminal for the module
    ccl = logging.getLogger('carboncollector')
    sh = StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(fmt='%(asctime)-15s %(name)-5s %(levelname)s %(message)s'))
    ccl.addHandler(sh)
    ccl.setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', required=False, metavar='cfgpath',
                        help='Path where the configuration file tagconfig.py can be found.',
                        default=CFGPATH)
    args = parser.parse_args()
    sys.path.append(args.p)

    import tagconfig as cfg
    sqluser = getattr(cfg, 'sqluser', None)
    sqlpw = getattr(cfg, 'sqlpw', None)
    sqldb = getattr(cfg, 'sqldb', None)
    sqlhost = getattr(cfg, 'sqlhost', None)

    c = TagCollector(sqluser=sqluser, sqlpw=sqlpw, sqldb=sqldb, sqlhost=sqlhost)
    c.collect(cfg.items, num_threads=getattr(cfg, 'num_threads', 1))


if __name__ == '__main__':
    main()
