# coding: utf-8

from conf import Config
from peewee import Model
from playhouse.pool import PooledMySQLDatabase


db = PooledMySQLDatabase(Config.DB_NAME, user=Config.DB_USER,
                         password=Config.DB_PASSWORD, host=Config.DB_HOST,
                         port=Config.DB_PORT, threadlocals=True, max_connections=Config.DB_POOL_MAX_CONNECTIONS,
                         stale_timeout=Config.DB_POOL_STALE_TIMEOUT)


class BaseModel(Model):

    class Meta:
        database = db
