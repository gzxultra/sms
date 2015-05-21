# coding: utf8
import functools
from requests.exceptions import ConnectionError, Timeout


class SMSSendFailed(Exception):
    pass


def retry_when_request_failed(retry_count):
    def wrap(func):
        @functools.wraps(func)
        def _(*args, **kwargs):
            for cnt in range(retry_count):
                try:
                    ret = func(*args, **kwargs)
                    return ret
                except (ConnectionError, Timeout):
                    pass
            else:
                raise SMSSendFailed('请求失败并超过重试次数')
        return _
    return wrap


class BaseClient(object):
    def send(self, country_code, phone_number, text):
        raise NotImplemented
