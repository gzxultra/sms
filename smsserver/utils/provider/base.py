# coding: utf-8
import requests
from threading import local


class Local(local):
    requests_session = None


class SMSSendFailed(Exception):
    pass


class BaseClient(object):

    def __init__(self, *args, **kw):
        self.__local = Local()

    def _get_request_session(self):
        if self.__local.requests_session is None:
            self.__local.requests_session = requests.Session()
        return self.__local.requests_session

    def _requests_get(self, *args, **kw):
        session = self._get_request_session()
        return session.get(*args, **kw)

    def _requests_post(self, *args, **kw):
        session = self._get_request_session()
        return session.post(*args, **kw)

    def send(self, country_code, phone_number, text, service_key):
        raise NotImplemented
