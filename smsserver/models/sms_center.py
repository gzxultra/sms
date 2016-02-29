# coding: utf8

import datetime
import random
import logging
from smsserver.models import Model
from smsserver.models.const import SMSSendStatus, SMSProviderIdent, ProviderServiceArea
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
        if country_code == '86':
            avaliable_provider_list = list(SMSProvider.where('weight > 0'))
        else:
            avaliable_provider_list = list(SMSProvider.where('service_area=%s and weight > 0', ProviderServiceArea.world_wide))
        avaliable_provider_num = len(avaliable_provider_list)

        for i in range(avaliable_provider_num):
            choices = [(provider, provider.weight) for provider in avaliable_provider_list]
            provider = _weighted_choice(choices)
            yield provider
            avaliable_provider_list.remove(provider)

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
            service_area = ProviderServiceArea.nation_wide
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
