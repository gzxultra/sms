# coding: utf-8


class DefaultConfig(object):
    THREAD_SAFE = False
    DEBUG = False
    DOMAIN = ''

    # 数据库配置
    DB_HOST = ''
    DB_PORT = 3306
    DB_USER = ''
    DB_PASSWORD = ''
    DB_NAME = ''
    DB_POOL_MAX_CONNECTIONS = 60
    DB_POOL_STALE_TIMEOUT = 300  # sec
    COMMIT_SELECT = True
    FAKE_MEMCACHED = False
    ENABLE_LOCAL_CACHED = True
    MEMCACHED_ADDR = (
        ('host:port', 'host:port'),
        ('host:port', 'host:port'),
    )

    BGTASK_MAX_WORKERS = 24

    # sentry 配置
    SENTRY_DSN = ''

    # 签名配置
    PUBLIC_KEY = ''  # 签名 public key
    SECRET_KEY = ''  # 签名 secret_key

    # mako 配置
    MAKO_TRANSLATE_EXCEPTIONS = False
    MAKO_FILESYSTEM_CHECKS = True
    MAKO_INPUT_ENCODING = 'utf8'
    MAKO_OUTPUT_ENCODING = 'utf8'

    TABLES = (
        'sms_provider',
        'sms_record',
        'sms_verification',
        'sms_verification_delivery',
        '*',
    )

    # 云片 apikey
    YUNPIAN_APIKEY = ''
