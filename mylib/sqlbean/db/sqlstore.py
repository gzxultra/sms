# -*- coding: UTF-8 -*-
import sys
import time
import MySQLdb
import warnings
from MySQLdb.converters import FIELD_TYPE, conversions
from _mysql_exceptions import (Warning, Error, InterfaceError, DataError, # noqa
     DatabaseError, OperationalError, IntegrityError, InternalError, # noqa
     NotSupportedError, ProgrammingError)
from connection import THREAD_SAFE
from transaction import Transaction


if THREAD_SAFE:
    from DBUtils.PersistentDB import PersistentDB as DB

    def connection(*args, **kwds):
        kwds['maxusage'] = False
        persist = DB(MySQLdb, *args, **kwds)
        conn = persist.connection()
        return conn

else:
    from DBUtils.SteadyDB import connect

    def connection(*args, **kwds):
        kwds['maxusage'] = False
        return connect(MySQLdb, *args, **kwds)


class LogCursor(object):
    def __init__(self, cursor):
        self._cursor = cursor
        self.log = []

    def execute(self, *a, **kw):
        t1 = time.time()
        try:
            retval = self._cursor.execute(*a, **kw)
        except:
            self.log.append((a, kw, 0))
            raise
        timecost = time.time() - t1
        self.log.append((a, kw, timecost))
        return retval

    def __iter__(self):
        return iter(self._cursor)

    def __getattr__(self, attr):
        return getattr(self._cursor, attr)


class CursorWrapper(object):
    def __init__(self, cursor, farm):
        self._cursor = cursor
        self.farm = farm

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __iter__(self):
        return iter(self._cursor)

    def _begin(self, sql):
        if not self.farm.commit_select and sql.lower().startswith('select'):
            # commit_select 为 False的时候，select语句不commit
            return
        self.farm.begin()

    def _commit(self, sql):
        if not self.farm.commit_select and sql.lower().startswith('select'):
            # commit_select 为 False的时候，select语句不commit
            return
        self.farm.commit()

    def _rollback(self, sql):
        if not self.farm.commit_select and sql.lower().startswith('select'):
            # commit_select 为 False的时候，select语句不commit
            return
        self.farm.rollback()

    def execute(self, sql, *args, **kwargs):
        if self.farm.execution_callback:
            self.farm.execution_callback(sql, *args, **kwargs)

        try:
            self._begin(sql)
            ret = self._cursor.execute(sql, *args, **kwargs)
            self._commit(sql)
            return ret
        except MySQLdb.OperationalError as e:
            error_no = e.args[0]
            if 2000 <= error_no < 3000:
                self.farm.close()
            raise
        except MySQLdb.ProgrammingError as e:
            if e.args[0] == 2014:
                self.farm.close()
            sys.stderr.write('%s %s\n' % (args, kwargs))
            raise
        except MySQLdb.IntegrityError, e:
            self._rollback(sql)
            raise


class SqlFarm(object):
    def __init__(self, host_str, **kwargs):
        self.dbcnf = self.parse_config_string(host_str)
        self.dbcnf.update(kwargs)
        self._conn = None
        self._cursor = None
        self.commit_select = self.dbcnf.pop('commit_select', True)
        self._transaction = None
        self.execution_callback = None

    @property
    def connection(self):
        if not self._conn:
            self._conn = self.connect(**self.dbcnf)
        return self._conn

    @property
    def transaction(self):
        if not self._transaction:
            self._transaction = Transaction(self.connection)
        return self._transaction

    def reopen(self):
        self._conn = None
        self._cursor = None
        self._transaction = None

    def set_execution_callback(self, callback):
        self.execution_callback = callback

    def connect(self, host, user, passwd, db, **kwargs):
        conn_params = dict(host=host, user=user,
                db=db, **kwargs)
        # 关闭autocommit，由ORM来处理transaction
        conn_params['autocommit'] = False
        if passwd:
            conn_params['passwd'] = passwd

        conv = conversions.copy()
        conv.update({
            FIELD_TYPE.TIMESTAMP: None,
            FIELD_TYPE.DATETIME: None,
            FIELD_TYPE.TIME: None,
            FIELD_TYPE.DATE: None,
        })

        conn_params['conv'] = conv
        conn = connection(**conn_params)

        if not conn:
            raise DatabaseError("can not connect to database: %s %s %s"
                         % (host, user, db))
        return conn

    def close(self):
        if self._conn:
            self._conn.close()

        self._conn = None
        self._cursor = None
        self._transaction = None

    def cursor(self):
        if self._cursor is None:
            self._cursor = CursorWrapper(self.connection.cursor(), self)
        return self._cursor

    def begin(self):
        self.transaction.begin()

    def commit(self):
        self.transaction.commit()

    def rollback(self):
        self.transaction.rollback()

    def is_in_transaction(self):
        return self.transaction.is_in_transaction()

    def force_commit(self):
        self.transaction.force_commit()

    def force_rollback(self):
        self.transaction.force_rollback()

    def start_log(self):
        if self._cursor is None:
            self._cursor = CursorWrapper(self.connection.cursor(), self)
        self._cursor = LogCursor(self._cursor)

    def stop_log(self):
        if self._cursor is not None:
            self._cursor = self._cursor._cursor

    def get_log(self, name):
        def sql_log(name, log):
            if log:
                return "%s: %d SQL statements (%s seconds):\n%s\n\n" % (
                    name, len(log), sum(x[2] for x in log),
                    "\n".join(["%8.6fsec %s" % (timecost, a)
                              for a, kw, timecost in log]))
            else:
                return "%s No Sql Log\n\n"%name
        so = sql_log(name, self._cursor.log)
        return so

    def parse_config_string(self, s):
        dummy = s.split(':')
        if len(dummy) == 4:
            host, db, user, passwd = dummy
            return dict(host=host, db=db, user=user, passwd=passwd)
        elif len(dummy) == 5:
            host, port, db, user, passwd = dummy
            return dict(host=host, port=int(port), db=db, user=user,
                    passwd=passwd)
        else:
            raise ValueError(s)


class SqlStore(object):
    def __init__(self, db_config, **connect_args):
        self.farms = {}
        self.tables = {}

        for name, f in db_config.items():
            farm = SqlFarm(f['master'], **connect_args)
            self.farms[name] = farm
            for table in f['tables']:
                self.tables[table] = farm

        if '*' not in self.tables:
            raise DatabaseError("No default farm specified")

    def close(self):
        for farm in self.farms.values():
            farm.close()

    def reopen(self):
        for farm in self.farms.values():
            farm.reopen()

    def get_farm(self, farm_name):
        farm = self.farms.get(farm_name)
        if farm is None:
            warnings.warn("Farm %r is not configured, use default farm" % farm_name,
                stacklevel=3)
            return self.tables['*']
        else:
            return farm

    def get_db_by_table(self, table):
        farm = self.tables.get(table)
        if farm is None:
            print "table not configure '%s'," % table
            return self.tables['*']
        else:
            return farm

    def cursor(self, table='*'):
        """get a cursor according to table"""
        farm = self.get_db_by_table(table)
        return farm.cursor()

    def start_log(self):
        for farm in self.farms.values():
            farm.start_log()

    def stop_log(self):
        for farm in self.farms.values():
            farm.stop_log()

    def get_log(self):
        r = ' '.join(farm.get_log(name) for name, farm in self.farms.items())
        return r

    def force_commit_all(self):
        for farm in self.farms.values():
            farm.force_commit()

    def force_rollback_all(self):
        for farm in self.farms.values():
            farm.force_rollback()

    def set_execution_callback(self, callback):
        for farm in self.farms.values():
            farm.set_execution_callback(callback)
