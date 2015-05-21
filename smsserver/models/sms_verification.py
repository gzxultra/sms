# coding: utf8
import datetime
import random
import string
from smsserver.models import Model
from smsserver.models.const import SMSVerificationStatus
from smsserver.models.sms_center import SMSCenter, SMSServiceTimeout


class SMSVerification(Model):
    class Meta(object):
        table = 'sms_verification'

        class default(object):
            id = None
            code = ''
            phone_number = ''
            country_code = ''
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now
            expire_time = lambda x: datetime.datetime.now() + datetime.timedelta(minutes=15)
            serial_number = ''
            status = SMSVerificationStatus.unused

    @classmethod
    def _generate_serial_number_and_code(cls):
        serial_number = ''.join([random.choice(string.ascii_letters+string.digits) for i in range(16)])
        code = ''.join([random.choice(string.digits) for i in range(6)])
        if cls.get(serial_number=serial_number, code=code):
            return cls._generate_serial_number_and_code()
        return serial_number, code

    @classmethod
    def create_or_get_unused_verification_code(cls, country_code, phone_number):
        '''创建或者获取一个未使用未过期的验证码。只有发送新验证码时才调用。过期时间设置为当前时间后15分钟'''
        now = datetime.datetime.now()
        obj_list = cls.where('country_code=%s and phone_number=%s and status=%s and %s <= expire_time',
                             country_code, phone_number, SMSVerificationStatus.unused, now).order_by('id desc')
        if obj_list:
            obj = obj_list[0]
            expire_time = now + datetime.timedelta(minutes=15)
            obj.update(expire_time=expire_time)
            return obj

        serial_number, code = cls._generate_serial_number_and_code()
        obj = cls(country_code=country_code, phone_number=phone_number,
                  serial_number=serial_number, code=code).save()
        return obj

    @classmethod
    def verify(cls, country_code, phone_number, serial_number, code):
        now = datetime.datetime.now()
        obj = cls.get(country_code=country_code,
                      phone_number=phone_number, serial_number=serial_number,
                      code=code)
        if not obj:
            return False

        expire_time = datetime.datetime.strptime(obj.expire_time, '%Y-%m-%d %H:%M:%S')

        if obj.status != SMSVerificationStatus.unused or now >= expire_time:
            return False
        obj.update(status=SMSVerificationStatus.used)
        return True

    @property
    def text(self):
        return u'【下厨房】验证码：%s，请在15分钟内完成验证。' % (self.code)

    def send_sms(self):
        try:
            self.begin()
            record = SMSCenter.send(self.country_code, self.phone_number, self.text)
            svd = SMSVerificationDelivery(sms_verification_id=self.id, smsid=record.id).save()
            self.commit()
        except SMSServiceTimeout:
            # 只捕获超时异常，HTTPError以及ConnectError不捕获
            self.rollback()
            return

    def is_send_success(self):
        return SMSVerificationDelivery.where(sms_verification_id=self.id).count() != 0


class SMSVerificationDelivery(Model):
    class Meta(object):
        table = 'sms_verification_delivery'

        class default(object):
            id = None
            sms_verification_id = None
            smsid = None
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now
