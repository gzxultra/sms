# coding: utf-8
import datetime
import random
import string
from smsserver.models import Model
from smsserver.models.const import SMSVerificationStatus
from smsserver.models.sms_center import SMSCenter


VERIFICATION_CODE_EXPIRE_MINUTES = 5
VERIFY_TIMES_LIMIT = 30


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
            expire_time = lambda x: datetime.datetime.now() + datetime.timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
            serial_number = ''
            status = SMSVerificationStatus.unused
            verify_times = 0

    @classmethod
    def _generate_serial_number_and_code(cls):
        serial_number = ''.join([random.choice(string.ascii_letters+string.digits) for i in range(16)])
        code = ''.join([random.choice(string.digits) for i in range(6)])
        if cls.get(serial_number=serial_number, code=code):
            return cls._generate_serial_number_and_code()
        return serial_number, code

    @classmethod
    def _get_unexpired_verification_code(cls, country_code, phone_number):
        '''获得当前未过期的验证码'''
        now = datetime.datetime.now()
        obj = cls.where('country_code=%s and phone_number=%s and status=%s and %s < expire_time',
                        country_code, phone_number, SMSVerificationStatus.unused, now).order_by('id desc')[0]
        return obj

    @classmethod
    def create_or_get_unused_verification_code(cls, country_code, phone_number):
        '''创建或者获取一个未使用未过期的验证码。只有发送新验证码时才调用。过期时间设置为当前时间后15分钟'''
        unexpired_verification_code = cls._get_unexpired_verification_code(country_code, phone_number)

        if unexpired_verification_code:
            now = datetime.datetime.now()
            expire_time = now + datetime.timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
            unexpired_verification_code.update(expire_time=expire_time)
            return unexpired_verification_code

        serial_number, code = cls._generate_serial_number_and_code()
        obj = cls(country_code=country_code, phone_number=phone_number,
                  serial_number=serial_number, code=code).save()
        return obj

    @classmethod
    def verify(cls, country_code, phone_number, code):
        obj = cls._get_unexpired_verification_code(country_code, phone_number)

        if not obj:
            return False

        # 验证码不正确
        if obj.code != code:
            obj.update(verify_times=obj.verify_times+1)
            return False

        # 验证次数超过限制, 返回验证失败
        if obj.verify_times >= VERIFY_TIMES_LIMIT:
            obj.update(expire_time=datetime.datetime.now(), verify_times=obj.verify_times+1)
            return False

        obj.update(status=SMSVerificationStatus.used, verify_times=obj.verify_times+1)
        return True

    @property
    def text(self):
        if self.country_code == '86':
            return u'验证码：%s，请在%s分钟内完成验证。' % (self.code, VERIFICATION_CODE_EXPIRE_MINUTES)
        else:
            return u'Your xiachufang.com phone verification pin is: %s' % self.code

    def send_sms(self):
        SMSCenter.send(self.country_code, self.phone_number, self.text)


class SMSVerificationDelivery(Model):

    class Meta(object):
        table = 'sms_verification_delivery'

        class default(object):
            id = None
            sms_verification_id = None
            smsid = None
            create_time = datetime.datetime.now
            update_time = datetime.datetime.now
