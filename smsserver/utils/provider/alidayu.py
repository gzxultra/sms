# coding: utf-8
import datetime
from collections import OrderedDict
from hmac import HMAC
from requests.exceptions import RequestException

from smsserver.utils.provider.base import BaseClient, SMSSendFailed


class ALiDaYuClient(BaseClient):
    DIGITS_DICT = {'0': u'零', '1': u'一', '2': u'二', '3': u'三', '4': u'四',
                   '5': u'五', '6': u'六', '7': u'七', '8': u'八', '9': u'九'}

    def __init__(self, apikey, secret, templates_dict, called_show_num):
        self.apikey = apikey
        self.secret = secret
        self.templates_dict = templates_dict
        self.called_show_num = called_show_num
        super(ALiDaYuClient, self).__init__()

    def send_sms(self, country_code, phone_number, text):
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
            'method': 'alibaba.aliqin.fc.sms.num.send',
            'rec_num': phone_number
        }
        data.update(self._text_map(text, self.templates_dict['sms']['templates'], 'sms_template_code', 'sms_param'))
        data['sign'] = self._generate_signature(data)
        return self._send(data, 'alibaba_aliqin_fc_sms_num_send_response')

    def send_voice(self, country_code, phone_number, text):
        data = {
            'app_key': self.apikey,
            'timestamp': datetime.datetime.now().strftime('%F %T'),
            'format': 'json',
            'v': '2.0',
            'sign_method': 'hmac',
            'method': 'alibaba.aliqin.fc.tts.num.singlecall',
            'called_num': phone_number,
            'called_show_num': self.called_show_num
        }
        data.update(self._text_map(text, self.templates_dict['voice']['templates'], 'tts_code', 'tts_param'))
        data['sign'] = self._generate_signature(data)
        return self._send(data, 'alibaba_aliqin_fc_tts_num_singlecall_response')

    def _send(self, data, response_key):
        try:
            ret = self._requests_post(url='https://eco.taobao.com/router/rest', data=data, timeout=5).json()
        except RequestException as e:
            raise SMSSendFailed(str(e))

        if 'error_response' in ret:
            error_messages = (ret['error_response']['code'],
                              ret['error_response']['msg'],
                              ret['error_response'].get('sub_code', ''),
                              ret['error_response'].get('sub_msg', ''))
            raise SMSSendFailed(u'阿里大于: %s %s %s %s' % error_messages)

        return {'outid': ret[response_key]['request_id']}

    def _text_map(self, text, templates, template_code_key, param_key):
        """根据传入的 text 映射为阿里大于的模板 id && 模板变量"""
        for template in templates:
            result = template['regex'].search(text)
            if result:
                return {
                    template_code_key: template['template_code'],
                    param_key: template['params'] % self._params_filter(result.groups(), template)
                }
        raise SMSSendFailed(u'阿里大于 无法匹配模板: %s' % text)

    def _generate_signature(self, data):
        ordered_data = OrderedDict(sorted(data.items(), key=lambda x: x[0]))
        params = []
        for k, v in ordered_data.iteritems():
            params.append(k)
            params.append(v)
        return HMAC(self.secret, u''.join(params).encode('utf-8')).hexdigest().upper()

    def _params_filter(self, params, template):
        if not template.get('to_chinese', False):
            return params
        return self._digits_to_chinese(params[0])  # params: ('123456', )

    def _digits_to_chinese(self, digits):
        return u''.join([self.DIGITS_DICT[digit] for digit in digits])
