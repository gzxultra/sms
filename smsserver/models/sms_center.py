# coding: utf8

import datetime
import random
from requests.exceptions import Timeout
from smsserver.models import Model
from smsserver.models.const import SMSSendStatus
from smsserver.utils.yunpian import YunPianV1, YunPianExceptionV1
from conf import Config


yunpian = YunPianV1(Config.YUNPIAN_APIKEY)


class SMSServiceTimeout(Exception):
    pass


class SMSSendFailed(Exception):
    def __init__(self, code, err_msg):
        self.code, self.err_msg = code, err_msg

    def __str__(self):
        return u'code: %s, err_msg: %s' % (self.code, self.err_msg)


class SMSCenter(object):
    @classmethod
    def choice_provider(cls):
        rand = random.randint(0, 100)
        provider = SMSProvider.where('%s <=start and %s < end', rand, rand)[0]

        if not provider:
            return SMSProvider.where()[0]
        return provider

    @classmethod
    def send(cls, country_calling_code, phone_number, text):
        if country_calling_code != '86':
            raise NotImplemented
        provider = cls.choice_provider()

        if provider.name == u'云片':
            try:
                ret = yunpian.send(phone_number, text)
            except Timeout:
                raise SMSServiceTimeout
            except YunPianExceptionV1, e:
                raise SMSSendFailed(e.code, '%s/%s' % (e.msg, e.detail))

            record = SMSRecord(country_calling_code=country_calling_code,
                               phone_number=phone_number, text=text,
                               provider_id=provider.id).save()
            fee_count, sid = ret['fee_count'], ret['sid']
            record.update(fee_count=fee_count, sid=sid, status=SMSSendStatus.success)
        else:
            raise NotImplemented

        return record


class SMSProvider(Model):
    class Meta(object):
        table = 'sms_provider'

        class default(object):
            id = None
            name = ''
            start = 0
            end = 0
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now

    @classmethod
    def create(cls, name, start=0, end=0):
        return cls(name=name, start=start, end=end).save()

    @classmethod
    def reset_weight(cls, d):
        '''
        d = {id: weight}
        '''
        if sum([v for k, v in d.iteritems()]) != 100:
            raise ValueError

        try:
            cls.begin()
            cls.where().update(start=0, end=0)
            cnt = 0
            for id_, weight in d.iteritems():
                start, end = cnt, cnt + weight
                cls.where(id=id_).update(start=start, end=end)
                cnt += weight
            cls.commit()
        except:
            cls.rollback()
            raise


class SMSRecord(Model):
    class Meta(object):
        table = 'sms_record'

        class default(object):
            id = None
            text = ''
            fee_count = None
            country_calling_code = ''
            phone_number = ''
            outid = None
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now
            receive_time = None
            error_msg = ''
            provider_id = None
            status = SMSSendStatus.initial
