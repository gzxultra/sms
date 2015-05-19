# coding: utf8

from conf.default import DefaultConfig


class Config(DefaultConfig):
    THREAD_SAFE = False
    DEBUG = True
    DOMAIN = ''

    # 数据库配置
    DB_HOST = ''
    DB_PORT = 3306
    DB_USER = ''
    DB_PASSWORD = ''
    DB_NAME = ''
    COMMIT_SELECT = True

    FAKE_MEMCACHED = True
    ENABLE_LOCAL_CACHED = True
    MEMCACHED_ADDR = (
        ('', ''),
    )

    # sentry 配置
    SENTRY_DSN = ''

    # 签名配置
    PUBLIC_KEY = ''
    SECRET_KEY = ''
