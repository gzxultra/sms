# coding: utf-8

import datetime
import random
import logging
import simplejson

from smsserver.models import BaseModel
from peewee import CharField, DateTimeField, IntegerField, TextField
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

        providers = [i for i in SMSProvider.select().where(SMSProvider.id.in_(provider_ids)) if i.weight > 0]

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


class SMSProvider(BaseModel):
    name = CharField()
    weight = IntegerField(default=1)
    ident = IntegerField()
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        db_table = 'sms_provider'

    @property
    def api_client(self):
        if self.ident == SMSProviderIdent.yunpian:
            return yunpianv1_client
        elif self.ident == SMSProviderIdent.dahansantong:
            return dahansantong_client
        raise NotImplemented

    def set_weight(self, weight):
        self.weight = weight
        self.save()

    def send(self, country_code, phone_number, text):
        api_client = self.api_client
        record = SMSRecord.create(country_code=country_code, phone_number=phone_number,
                                  text=text, provider_id=self.id)
        try:
            ret = api_client.send(country_code, phone_number, text)
        except SMSSendFailed as e:
            record.statue, record.err_msg = SMSSendStatus.failed, e.message
            record.save()
            raise e
        else:
            record.statue, record.err_msg = SMSSendStatus.success, ret['outid']
            record.save()
        return record


class SMSRecord(BaseModel):
    text = CharField()
    phone_number = CharField()
    country_code = CharField()
    outid = CharField()
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now)
    receive_time = DateTimeField()
    error_msg = CharField()
    provider_id = IntegerField()
    status = IntegerField(default=SMSSendStatus.initial)

    class Meta:
        db_table = 'sms_record'


class OutOfServiceArea(Exception):
    pass


class SMSProviderServiceArea(BaseModel):
    country_code = CharField(index=True)
    providers_json = TextField(default='{}')

    class Meta:
        db_table = 'sms_provider_service_area'

    @classmethod
    def set_avaliable_sms_providers(cls, country_code, providers):
        obj = cls.select().where(cls.country_code == country_code.strip()).first()
        if obj:
            obj = cls.create(country_code=country_code.strip())
        d = {'provider_ids': [i.id for i in providers]}
        obj.provider_json = simplejson.dumps(d)
        obj.save()

    @classmethod
    def get_avaliable_sms_providers(cls, country_code):
        obj = cls.select().where(cls.country_code == country_code.strip()).first()
        if not obj:
            raise OutOfServiceArea

        d = simplejson.loads(obj.providers_json)
        return [i for i in d.get('provider_ids', [])]
