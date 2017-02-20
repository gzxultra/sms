# coding: utf-8

import datetime
import logging
import random

import simplejson
from conf import Config
from peewee import CharField, DateTimeField, IntegerField, TextField
from smsserver.bgtask import spawn_bgtask
from smsserver.models import BaseModel
from smsserver.models.const import SMSProviderIdent, SMSSendStatus
from smsserver.utils.provider import (
    SMSSendFailed, alidayu_client, dahansantong_client, yunpianv1_client
)

VERIFICATION_CODE_EXPIRE_MINUTES = Config.VERIFICATION_CODE_EXPIRE_MINUTES
VERIFY_TIMES_LIMIT = Config.VERIFY_TIMES_LIMIT

send_sms_logger = logging.getLogger('send_sms')


def _get_service_key(is_sms):
    return 'sms' if is_sms else 'voice'


def _weighted_providers(providers, country_code, phone_number):
    """按权重并结合随机数对providers排序"""
    now = datetime.datetime.now()
    expire_time = now + datetime.timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
    used_provider_ids = SMSRecord.select(SMSRecord.provider_id).where(
        SMSRecord.update_time.between(now, expire_time) &
        (phone_number == phone_number) &
        (country_code == country_code)
    )

    choices = []
    for provider in providers:
        weight = provider.weight * random.random()
        # 降低已用过服务的权重
        if provider.id in used_provider_ids:
            weight = weight / 1000.0
        choices.append((weight, provider))
    return [p for __, p in sorted(choices, reverse=True)]


class SMSCenter(object):

    @classmethod
    def _yield_provider(cls, country_code, phone_number, service_key):
        try:
            provider_ids = SMSProviderServiceArea.get_avaliable_sms_providers(country_code, service_key)
        except OutOfServiceArea:
            raise SMSSendFailed(u'短信无法发送至该地区')
        providers = SMSProvider.select().where(
            SMSProvider.id.in_(provider_ids) &
            SMSProvider.weight > 0
        )
        return _weighted_providers(providers, country_code, phone_number)

    @classmethod
    def _send(cls, country_code, phone_number, text, service_key):
        for provider in cls._yield_provider(country_code, phone_number, service_key):
            try:
                ret = provider.send(country_code, phone_number, text, service_key)
                return ret
            except SMSSendFailed as e:
                send_sms_logger.error('sms_send_failed,%s %s' % (phone_number, e.message))
                continue

        raise SMSSendFailed

    @classmethod
    def _send_no_raise(cls, country_code, phone_number, text, service_key):
        try:
            cls._send(country_code, phone_number, text, service_key)
        except SMSSendFailed as e:
            send_sms_logger.error('sms_send_failed,%s %s' % (phone_number, e.message))

    @classmethod
    def send(cls, country_code, phone_number, text, is_async=True, is_sms=True):
        if is_async:
            spawn_bgtask(cls._send_no_raise, country_code=country_code, phone_number=phone_number, text=text,
                         service_key=_get_service_key(is_sms))
            return
        cls._send(country_code=country_code, phone_number=phone_number, text=text, service_key=_get_service_key(is_sms))


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
        elif self.ident == SMSProviderIdent.alidayu:
            return alidayu_client
        raise NotImplementedError()

    def set_weight(self, weight):
        self.weight = weight
        self.save()

    def send(self, country_code, phone_number, text, service_key):
        api_client = self.api_client
        record = SMSRecord.create(country_code=country_code, phone_number=phone_number,
                                  text=text, provider_id=self.id)
        try:
            if service_key == 'sms':
                ret = api_client.send_sms(country_code, phone_number, text)
            else:
                ret = api_client.send_voice(country_code, phone_number, text)
        except SMSSendFailed as e:
            record.status, record.err_msg = SMSSendStatus.failed, e.message
            record.save()
            raise e
        else:
            record.status, record.err_msg = SMSSendStatus.success, ret['outid']
            record.save()
        return record


class SMSRecord(BaseModel):
    text = CharField()
    phone_number = CharField(index=True)
    country_code = CharField(index=True)
    outid = CharField()
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now, index=True)
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
    def set_avaliable_sms_providers(cls, country_code, providers, is_sms=True):
        obj = cls.select().where(cls.country_code == country_code.strip()).first()
        if obj:
            obj = cls.create(country_code=country_code.strip())
        providers_dict = simplejson.loads(obj.providers_json)
        providers_dict[_get_service_key(is_sms)] = {'provider_ids': [i.id for i in providers]}
        obj.provider_json = simplejson.dumps(providers_dict)
        obj.save()

    @classmethod
    def get_avaliable_sms_providers(cls, country_code, service_key):
        obj = cls.select().where(cls.country_code == country_code.strip()).first()
        if not obj:
            raise OutOfServiceArea

        providers_dict = simplejson.loads(obj.providers_json).get(service_key, {})
        return providers_dict.get('provider_ids', [])
