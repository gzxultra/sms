# coding: utf8

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import warnings
import MySQLdb
from mylib.sqlbean import SQLBean
from conf import Config

try:
    from uwsgidecorators import postfork
except ImportError:
    postfork = lambda f: f


if Config.DEBUG:
    warnings.filterwarnings('error', category=MySQLdb.Warning)


db = SQLBean(
    db_config={
        'db_config': {
            'xcf_sms': {
                'master': '%s:%s:%s:%s' % (Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD),
                'tables': Config.TABLES
            }
        },
        'commit_select': Config.COMMIT_SELECT
    },
    mc_config={
        'MEMCACHED_ADDR': Config.MEMCACHED_ADDR,
        'ENABLE_LOCAL_CACHED': Config.ENABLE_LOCAL_CACHED,
        'FAKE_MEMCACHED': Config.FAKE_MEMCACHED
    }
)


@postfork
def uwsgi_postfork():
    db.reopen()


from mylib.sqlbean.shortcut import Query, mc, Model, McModel  # noqa
