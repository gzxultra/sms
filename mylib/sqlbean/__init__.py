#coding: utf8
from mylib.sqlbean.db import mc_connection
from mylib.sqlbean.db import connection
from mylib.sqlbean.db import sqlstore
from mylib.sqlbean.metamodel import cache as model_cache
from mylib.sqlbean.db.mc_client import setup_memcache


class SQLBean(object):

    def __init__(self, db_config={}, mc_config={}, thread_safe=False):
        '''
        db_config={
            'db_config': DATABASE_CONFIG,
            'commit_select': COMMIT_SELECT,
            }

        mc_config={
            'MEMCACHED_ADDR': ((group1_addr1, group1_addr2), (group2_addr1, group2_addr2)),
            'ENABLE_LOCAL_CACHED': ENABLE_LOCAL_CACHED,
            'FAKE_MEMCACHED': FAKE_MEMCACHED
        }
        '''
        default_db_config = {
            'charset': 'utf8',
            'local_infile': True,
            'commit_select': True,
            'init_command': 'set names utf8',
        }
        default_db_config.update(db_config)
        self.db_config = default_db_config
        self.mc_config = mc_config
        self.thread_safe = thread_safe
        self.sqlstore = self.init_db()
        self.mc = self.init_mc()

    def __getattr__(self, *args, **kwargs):
        return getattr(self.sqlstore, *args, **kwargs)

    @property
    def models(self):
        return model_cache.models.values()

    def init_mc(self):
        mc = setup_memcache(
            memcached_addrs=self.mc_config.get('MEMCACHED_ADDR', []),
            enable_local_cached=self.mc_config.get('ENABLE_LOCAL_CACHED', False),
            fake=self.mc_config.get('FAKE_MEMCACHED', False)
        )
        mc_connection.mc = mc
        return mc

    def init_db(self):
        db_config = self.db_config.copy()
        store = sqlstore.SqlStore(db_config=db_config.pop('db_config'), **db_config)
        connection.get_db_by_table = store.get_db_by_table
        connection.THREAD_SAFE = self.thread_safe
        return store

    def commit(self):
        try:
            self.sqlstore.force_commit_all()
        except:
            pass

    def close(self):
        if self.sqlstore:
            self.sqlstore.close()
        self.sqlstore = None

    def reopen(self):
        self.sqlstore.reopen()
        self.mc.reopen()

    def hook_execution(self, callback):
        self.sqlstore.set_execution_callback(callback)
