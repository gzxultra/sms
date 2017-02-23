# coding: utf-8


class DefaultConfig(object):
    THREAD_SAFE = False
    DEBUG = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
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

    BGTASK_MAX_WORKERS = 20

    # 验证码配置
    VERIFICATION_CODE_EXPIRE_MINUTES = 5
    VERIFY_TIMES_LIMIT = 10

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

    # 云片 apikey
    YUNPIAN_APIKEY = ''

    # 大汉三通 account password
    DAHANSANTONG_ACCOUNT = ''
    DAHANSANTONG_PASSWORD = ''

    # 阿里大鱼 key secret templates
    ALIDAYU_KEY = ''
    ALIDAYU_SECRET = ''
    ALIDAYU_CALLED_SHOW_NUM = ''
    ALIDAYU_TEMPLATES_DICT = {
        'sms': {
            'templates': (
                {
                    'regex': 'compiled regex',
                    'params': '',
                    'template_code': ''
                },
            ),
        },
        'voice': {
            'templates': (
                {
                    'regex': 'compiled regex',
                    'params': '',
                    'template_code': '',
                    'to_chinese': True  # 需要转换成汉字
                },
            ),
        }
    }

    STATSD_HOST = 'localhost'
    STATSD_PORT = 8125
