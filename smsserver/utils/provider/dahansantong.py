# coding: utf-8

import requests
import hashlib
import xml.etree.ElementTree as ET
from smsserver.utils.provider.base import BaseClient, SMSSendFailed


class DahanSanTongClient(BaseClient):
    SEND_URL = 'http://wt.3tong.net/http/sms/Submit'

    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.password_md5 = hashlib.md5(password).hexdigest()
        super(DahanSanTongClient, self).__init__(account, password)

    def send(self, country_code, phone_number, text):
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
        <message>
            <account>%(account)s</account>
            <password>%(password)s</password>
            <msgid></msgid>
            <phones>%(phones)s</phones>
            <content>%(content)s</content>
            <sign>【下厨房】</sign>
            <subcode></subcode>
            <sendtime></sendtime>
        </message>'''
        url = self.SEND_URL
        d = {'account': self.account, 'password': self.password_md5,
             'phones': phone_number, 'content': text}
        message = xml_template % d
        ret = {}

        try:
            r = self._requests_post(url, {'message': message}, timeout=5)
            root = ET.fromstring(r.text)
            for node in root:
                ret[node.tag] = node.text
        except (requests.exceptions.RequestException), e:
            raise SMSSendFailed(str(e))

        if int(ret['result']) != 0:
            raise SMSSendFailed('大汉三通: %s %s' % (ret['result'], ret['desc']))
        return {'outid': ret['msgid']}
