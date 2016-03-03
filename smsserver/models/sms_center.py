# coding: utf-8

import datetime
import random
import logging
import simplejson

from smsserver.models import Model
from smsserver.models.const import SMSSendStatus, SMSProviderIdent
from smsserver.utils.provider import SMSSendFailed, yunpianv1_client, dahansantong_client


send_sms_logger = logging.getLogger('send_sms')


def _weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w


class SMSCenter(object):

    @classmethod
    def _yield_provider(cls, country_code, phone_number):
        try:
            provider_ids = SMSProviderServiceArea.get_avaliable_sms_providers(country_code)
        except OutOfServiceArea:
            raise SMSSendFailed(u'短信无法发送至该地区')

        providers = [i for i in SMSProvider.get_list(provider_ids) if i.weight > 0]

        avaliable_provider_num = len(providers)

        for i in range(avaliable_provider_num):
            choices = [(provider, provider.weight) for provider in providers]
            provider = _weighted_choice(choices)
            yield provider
            providers.remove(provider)

    @classmethod
    def send(cls, country_code, phone_number, text):
        for provider in cls._yield_provider(country_code, phone_number):
            try:
                ret = provider.send(country_code, phone_number, text)
                return ret
            except SMSSendFailed as e:
                send_sms_logger.error('sms_send_failed,%s %s' % (phone_number, e.message))
                continue

        raise SMSSendFailed


class SMSProvider(Model):

    class Meta(object):
        table = 'sms_provider'

        class default(object):
            id = None
            name = ''
            weight = 1
            ident = None
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now

    @classmethod
    def create(cls, name, ident, weight):
        return cls(name=name, ident=ident, weight=weight).save()

    @property
    def api_client(self):
        if self.ident == SMSProviderIdent.yunpian:
            return yunpianv1_client
        elif self.ident == SMSProviderIdent.dahansantong:
            return dahansantong_client
        raise NotImplemented

    def set_weight(self, weight):
        self.update(weight=weight)

    def send(self, country_code, phone_number, text):
        api_client = self.api_client
        record = SMSRecord(country_code=country_code, phone_number=phone_number,
                           text=text, provider_id=self.id).save()
        try:
            ret = api_client.send(country_code, phone_number, text)
        except SMSSendFailed, e:
            record.update(status=SMSSendStatus.failed, err_msg=e.message)
            raise e
        else:
            record.update(status=SMSSendStatus.success, outid=ret['outid'])
        return record


class SMSRecord(Model):

    class Meta(object):
        table = 'sms_record'

        class default(object):
            id = None
            text = ''
            country_code = ''
            phone_number = ''
            outid = None
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now
            receive_time = None
            error_msg = ''
            provider_id = None
            status = SMSSendStatus.initial


class OutOfServiceArea(Exception):
    pass


class SMSProviderServiceArea(Model):

    class Meta(object):
        table = 'sms_provider_service_area'

        class default(object):
            id = None
            country_code = ''
            providers_json = '{}'

    @classmethod
    def set_avaliable_sms_providers(cls, country_code, providers):
        obj = cls.get(country_code=country_code.strip())
        if not obj:
            obj = cls(country_code=country_code.strip()).save()
        d = {'provider_ids': [i.id for i in providers]}
        obj.update(providers_json=simplejson.dumps(d))

    @classmethod
    def get_avaliable_sms_providers(cls, country_code):
        obj = cls.get(country_code=country_code.strip())
        if not obj:
            raise OutOfServiceArea

        d = simplejson.loads(obj.providers_json)
        return [i for i in d.get('provider_ids', [])]
