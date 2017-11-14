import logging
from .collector import escape_carbon
from .collector import Collector
import MySQLdb

log = logging.getLogger(__name__)


class TagCollector(Collector):
    def __init__(self, sqluser=None, sqlpw=None, sqldb=None, sqlhost=None):
        self.sqluser = sqluser
        self.sqlpw = sqlpw
        self.sqldb = sqldb
        self.sqlhost = sqlhost

    def store_data(self, data, prefix=None):
        # create table tags (k varchar(500) NOT NULL, v varchar(1000) NOT NULL, timestamp timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY(k));
        for item in data:
            _ = []
            if prefix:
                _ = [escape_carbon(a) for a in prefix]
            _.extend([escape_carbon(a) for a in item.path])
            path = '.'.join(_)
            # write the path as key into the database
            self.c.execute('replace into tags (k, v) values(%s, %s)', ('name=' + path, item.value))
            log.debug('%s -> %s' % (path, item.value))
            for k, v in item.tags.items():
                tag = 'tag_' + '='.join((k,v))
                self.c.execute('replace into tags (k, v) values(%s, %s)', (tag, path))
                log.debug('%s -> %s' % (tag, path))

    def _worker(self, q, resultq):
        # we need a sql connection per worker - this is why the connection is not
        # created from the __init__ method!
        self.db = MySQLdb.connect(user=self.sqluser, passwd=self.sqlpw, db=self.sqldb, host=self.sqlhost)
        self.db.autocommit(on=True)
        self.c = self.db.cursor()
        return super(TagCollector, self)._worker(q, resultq)
