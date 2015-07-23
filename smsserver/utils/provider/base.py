# coding: utf8
import functools
from requests.exceptions import ConnectionError, Timeout


class SMSSendFailed(Exception):
    pass


class BaseClient(object):
    def send(self, country_code, phone_number, text):
        raise NotImplemented
