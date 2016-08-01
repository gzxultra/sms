# coding: utf-8
import datetime
from collections import OrderedDict
from hmac import HMAC
from requests.exceptions import RequestException

from smsserver.utils.provider.base import BaseClient, SMSSendFailed


class ALiDaYuClient(BaseClient):
    URL = 'https://eco.taobao.com/router/rest'

    def __init__(self, apikey, secret, regexs):
        self.apikey = apikey
        self.secret = secret
        self.regexs = regexs
        super(ALiDaYuClient, self).__init__()

    def send(self, country_code, phone_number, text):
        """
        :param country_code: 国家区号(阿里大于目前只能发+86的号码, 所以这个参数并无卵用)
        :param phone_number: 手机号码
        :param text: 文本内容
        :return: {'outid': u'z2c11bel02er'}
        """

        data = {
            'app_key': self.apikey,
            'timestamp': datetime.datetime.now().strftime('%F %T'),
            'format': 'json',
            'v': '2.0',
            'sign_method': 'hmac',
            'sms_type': 'normal',
            'sms_free_sign_name': u'下厨房',
            'rec_num': phone_number,
            'method': 'alibaba.aliqin.fc.sms.num.send',
        }
        data.update(self._magic_map(text))
        data['sign'] = self._generate_signature(data)

        try:
            ret = self._requests_post(self.URL, data=data, timeout=5).json()
        except RequestException as e:
            raise SMSSendFailed(str(e))

        if 'error_response' in ret:
            error_messages = (ret['error_response']['code'],
                              ret['error_response']['msg'],
                              ret['error_response'].get('sub_code', ''),
                              ret['error_response'].get('sub_msg', ''))
            raise SMSSendFailed(u'阿里大于: %s %s %s %s' % error_messages)

        return {'outid': ret['alibaba_aliqin_fc_sms_num_send_response']['request_id']}

    def _magic_map(self, text):
        """根据传入的 text 映射为阿里大于的模板 id && 模板变量"""
        for regex, param_template, template_code in self.regexs:
            result = regex.search(text)
            if result:
                return {'sms_template_code': template_code, 'sms_param': param_template % result.groups()}
        raise SMSSendFailed(u'阿里大于 无法匹配模板: %s' % text)

    def _generate_signature(self, data):
        ordered_data = OrderedDict(sorted(data.items(), key=lambda x: x[0]))
        params = []
        for key in ordered_data:
            params.append(key)
            params.append(ordered_data[key])
        return HMAC(self.secret, u''.join(params).encode('utf-8')).hexdigest().upper()
