# coding: utf8

import functools
import requests
from urllib import urlencode
from requests.exceptions import ConnectionError, Timeout


def retry_when_request_failed(func):
    @functools.wraps(func)
    def _(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except (ConnectionError, Timeout):
            return func(*args, **kwargs)
        else:
            return ret
    return _


class YunPianExceptionV1(Exception):
    def __init__(self, code, msg, detail):
        self.code, self.msg, self.detail = code, msg, detail

    def __str__(self):
        return '%s %s %s' % (self.code, self.msg, self.detail)


class YunPianV1(object):
    DOMAIN = 'http://yunpian.com'

    def __init__(self, apikey):
        self.apikey = apikey

    @retry_when_request_failed
    def send(self, mobile, text):
        '''
        mobile: 国内电话号码 text: 文本内容
        返回值: {'fee_count': xxx, 'sid': xxx} fee_count表示扣费条数(70个字一条，超出70个字时按每67字一条计), sid表示短信id
        '''
        url = '%s/%s' % (self.DOMAIN, 'v1/sms/send.json')
        d = {'apikey': self.apikey, 'mobile': mobile, 'text': text}
        ret = requests.post(url, data=d, timeout=5).json()

        if ret['code'] != 0:
            raise YunPianExceptionV1(ret['code'], ret['msg'], ret['detail'])

        return {'fee_count': int(ret['result']['fee']), 'sid': ret['result']['sid']}

    @retry_when_request_failed
    def tmp_send(self, mobile, tpl_id, value):
        '''
        mobile: 国内电话号码 tpl_id: 模版id tpl_value: 模版变量
        返回值: {'fee_count': xxx, 'sid': xxx} fee_count表示扣费条数(70个字一条，超出70个字时按每67字一条计), sid表示短信id
        '''
        url = '%s/%s' % (self.DOMAIN, 'v1/sms/tpl_send.json')
        _tpl_value_dict = {'#%s#' % k: v for k, v in value.iteritems()}
        tpl_value = urlencode(_tpl_value_dict)
        d = {'apikey': self.apikey, 'mobile': mobile, 'tpl_id': tpl_id, 'tpl_value': tpl_value}
        ret = requests.post(url, data=d, timeout=5).json()

        if ret['code'] != 0:
            raise YunPianExceptionV1(ret['code'], ret['msg'], ret['detail'])

        return {'fee_count': ret['result']['fee'], 'sid': ret['result']['sid']}

    @retry_when_request_failed
    def pull_status(self, size=20):
        '''拉取短信发送状态，已成功获取的数据api不会再次返回
        返回值: (has_more, status_list)
        has_more: True || False
        status_list: [{'sid': 短信id, 'receive_time': '接收时间', 'error_msg': '接受失败的原因', 'mobile': '接受手机号', 'status': 'SUCCESS/FAIL/UNKNOWN'}]
        '''
        url = '%s/%s' % (self.DOMAIN, 'v1/sms/pull_status.json')
        d = {'apikey': self.apikey, 'page_size': size}
        ret = requests.post(url, data=d).json()

        if ret['code'] != 0:
            raise YunPianExceptionV1(ret['code'], ret['msg'], ret['detail'])

        _status_list = ret['sms_status']
        has_more = len(_status_list) == size
        status_list = [{'sid': i['sid'], 'receive_time': i['user_receive_time'],
                        'error_msg': i['error_msg'], 'mobile': i['mobile']}
                       for i in _status_list]
        return (has_more, status_list)

    @retry_when_request_failed
    def pull_reply(self, size):
        '''
        拉取短信回复数据，已成功获取的数据api不会再次返回
        返回值: (has_more, reply_list)
        has_more: True || False
        status_list: [{'reply_time': '回复时间', 'mobile': '接受手机号', 'text': '回复内容'}]
        '''
        url = '%s/%s' % (self.DOMAIN, 'v1/sms/pull_reply.json')
        d = {'apikey': self.apikey, 'page_size': size}
        ret = requests.post(url, data=d).json()

        if ret['code'] != 0:
            raise YunPianExceptionV1(ret['code'], ret['msg'], ret['detail'])

        _reply_list = ret['sms_reply']
        has_more = len(_reply_list) == size
        reply_list = [{'reply_time': i['reply_time'], 'mobile': i['mobile'],
                       'text': i['text']}
                      for i in _reply_list]
        return (has_more, reply_list)

    @retry_when_request_failed
    def get_black_word(self, text):
        '''查询短信中包括的屏蔽词
        返回列表。内容是屏蔽词
        '''
        url = '%s/%s' % (self.DOMAIN, 'v1/sms/get_black_word.json')
        d = {'apikey': self.apikey, 'text': text}
        ret = requests.post(url, data=d).json()

        if ret['code'] != 0:
            raise YunPianExceptionV1(ret['code'], ret['msg'], ret['detail'])

        black_word_str = ret['result']['black_word'] or ''
        return black_word_str.split(',')
