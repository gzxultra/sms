# coding: utf-8
import datetime
import logging

import simplejson
from peewee import CharField, DateTimeField, IntegerField, TextField
from smsserver.bgtask import spawn_bgtask
from smsserver.models import BaseModel
from smsserver.models.const import SMSProviderIdent, SMSSendStatus
from smsserver.utils.provider import (
    SMSSendFailed, alidayu_client, dahansantong_client, yunpianv1_client
)
from smsserver.utils.weighted_shuffle import weighted_shuffle

send_sms_logger = logging.getLogger('send_sms')


class OutOfServiceArea(Exception):
    pass


def _get_service_key(is_sms):
    return 'sms' if is_sms else 'voice'


def _get_used_provider_ids(country_code, phone_number, minutes=30):
    now = datetime.datetime.now()
    past = now - datetime.timedelta(minutes=minutes)
    used_providers = SMSRecord\
        .select(SMSRecord.provider_id)\
        .distinct()\
        .where(
            SMSRecord.create_time.between(past, now) &
            (SMSRecord.phone_number == phone_number) &
            (SMSRecord.country_code == country_code)
        )
    return [x.provider_id for x in used_providers]


def _get_providers(country_code, phone_number, service_key):
    try:
        provider_ids = SMSProviderServiceArea.get_avaliable_sms_providers(country_code, service_key)
    except OutOfServiceArea:
        raise SMSSendFailed(u'短信无法发送至该地区')
    providers = SMSProvider.select().where(
        SMSProvider.id.in_(provider_ids) &
        SMSProvider.weight > 0
    )
    return providers


def _get_weighted_providers(country_code, phone_number, service_key):
    """按权重并结合随机数打乱providers顺序"""
    providers = _get_providers(country_code, phone_number, service_key)
    used_provider_ids = _get_used_provider_ids(country_code, phone_number)
    choices = []
    for provider in providers:
        weight = provider.weight
        # 降低已用过服务的权重
        if provider.id in used_provider_ids:
            weight = weight / 1000.0
        choices.append((provider, weight))
    return weighted_shuffle(choices)


def _send(country_code, phone_number, text, service_key):
    for provider in _get_weighted_providers(country_code, phone_number, service_key):
        try:
            return provider.send(country_code, phone_number, text, service_key)
        except SMSSendFailed as e:
            send_sms_logger.error('sms_send_failed,%s %s' % (phone_number, e.message))
            continue
    raise SMSSendFailed


def _send_no_raise(country_code, phone_number, text, service_key):
    try:
        _send(country_code, phone_number, text, service_key)
    except SMSSendFailed as e:
        send_sms_logger.error('sms_send_failed,%s %s' % (phone_number, e.message))


class SMSCenter(object):

    @classmethod
    def send(cls, country_code, phone_number, text, is_async=True, is_sms=True):
        service_key = _get_service_key(is_sms)
        params = dict(
            country_code=country_code,
            phone_number=phone_number,
            text=text,
            service_key=service_key
        )
        if is_async:
            spawn_bgtask(_send_no_raise, **params)
        else:
            _send(**params)


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
            # record.error_msg 最长 128，切掉尾巴
            if isinstance(e.message, str):
                error_msg = e.message.decode('utf-8')
            else:
                error_msg = e.message
            if len(error_msg) > 128:
                error_msg = u"{}...".format(error_msg[:125])
            record.status, record.error_msg = SMSSendStatus.failed, error_msg
            record.save()
            raise e
        else:
            record.status, record.outid = SMSSendStatus.success, ret['outid']
            record.save()
        return record


class SMSRecord(BaseModel):
    text = CharField()
    phone_number = CharField(index=True)
    country_code = CharField()
    outid = CharField()
    create_time = DateTimeField(default=datetime.datetime.now, index=True)
    update_time = DateTimeField(default=datetime.datetime.now)
    receive_time = DateTimeField()
    error_msg = CharField()
    provider_id = IntegerField()
    status = IntegerField(default=SMSSendStatus.initial)

    class Meta:
        db_table = 'sms_record'


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
