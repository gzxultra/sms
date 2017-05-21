# coding: utf-8
import datetime
import random
import string
from smsserver.models import BaseModel
from smsserver.models.const import SMSVerificationStatus
from smsserver.models.sms_center import SMSCenter
from peewee import CharField, DateTimeField, IntegerField
from conf import Config

VERIFICATION_CODE_EXPIRE_MINUTES = Config.VERIFICATION_CODE_EXPIRE_MINUTES
VERIFY_TIMES_LIMIT = Config.VERIFY_TIMES_LIMIT


class SMSVerification(BaseModel):
    code = CharField()
    phone_number = CharField()
    country_code = CharField()
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now)
    expire_time = DateTimeField(default=lambda: datetime.datetime.now() + datetime.timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES))
    serial_number = CharField(index=True)
    status = IntegerField(default=SMSVerificationStatus.unused)
    verify_times = IntegerField(default=0)

    class Meta:
        db_table = 'sms_verification'
        indexes = ((('country_code', 'phone_number', 'status', 'expire_time'), False),)

    @classmethod
    def _generate_serial_number_and_code(cls):
        serial_number = ''.join([random.choice(string.ascii_letters+string.digits) for i in range(16)])
        code = ''.join([random.choice(string.digits) for i in range(6)])
        if cls.select().where((cls.serial_number == serial_number) & (cls.code == code)).count():
            return cls._generate_serial_number_and_code()
        return serial_number, code

    @classmethod
    def _get_unexpired_verification_code(cls, country_code, phone_number):
        '''获得当前未过期的验证码'''
        now = datetime.datetime.now()
        obj = cls.select().where((cls.country_code == country_code) & (cls.phone_number == phone_number) &
                                 (cls.status == SMSVerificationStatus.unused) & (cls.expire_time > now)).order_by(cls.id).first()
        return obj

    @classmethod
    def create_or_get_unused_verification_code(cls, country_code, phone_number):
        '''创建或者获取一个未使用未过期的验证码。只有发送新验证码时才调用。过期时间设置为当前时间后15分钟'''
        unexpired_verification_code = cls._get_unexpired_verification_code(country_code, phone_number)

        if unexpired_verification_code:
            now = datetime.datetime.now()
            expire_time = now + datetime.timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
            unexpired_verification_code.expire_time = expire_time
            unexpired_verification_code.save()
            return unexpired_verification_code

        serial_number, code = cls._generate_serial_number_and_code()
        obj = cls.create(country_code=country_code, phone_number=phone_number,
                  serial_number=serial_number, code=code)
        return obj

    @classmethod
    def verify(cls, country_code, phone_number, code):
        obj = cls._get_unexpired_verification_code(country_code, phone_number)

        if not obj:
            return False

        # 验证码不正确
        if obj.code != code:
            obj.verify_times += 1
            obj.save()
            return False

        # 验证次数超过限制, 返回验证失败
        if obj.verify_times >= VERIFY_TIMES_LIMIT:
            obj.expire_time, obj.verify_times = datetime.datetime.now(), obj.verify_times + 1
            obj.save()
            return False

        obj.status, obj.verify_times = SMSVerificationStatus.used, obj.verify_times + 1
        obj.save()
        return True

    @property
    def text(self):
        # 大陆、港澳台发送简体中文，其他地区发送英文
        if self.country_code in ('86', '852', '853', '886'):
            return u'验证码：%s，请在%s分钟内完成验证。' % (self.code, VERIFICATION_CODE_EXPIRE_MINUTES)
        else:
            return u'Your confirmation code is %s, please verify in %s minutes.' % (self.code, VERIFICATION_CODE_EXPIRE_MINUTES)

    def send(self, signer='下厨房', is_async=True, is_sms=True):
        SMSCenter.send(signer, self.country_code, self.phone_number, self.text, is_async=is_async, is_sms=is_sms)
