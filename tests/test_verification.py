# coding: utf8
import pytest
from smsserver.models.sms_verification import SMSVerification

COUNTRY_CALLING_CODE = '86'
PHONE_NUMBER = '18510238421'


@pytest.fixture
def unused_and_not_expired_verification(scope='module'):
    country_calling_code = COUNTRY_CALLING_CODE
    phone_number = PHONE_NUMBER
    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_calling_code, phone_number)
    return sms_verification


def test_verify_with_valid_code():
    country_calling_code = '86'
    phone_number = '18510238421'
    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_calling_code, phone_number)
    assert SMSVerification.verify(country_calling_code, phone_number, sms_verification.serial_number,
                                  sms_verification.code)


def test_verify_with_valid_code1():
    country_calling_code = '86'
    phone_number = '18510238421'
    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_calling_code, phone_number)
    assert False == SMSVerification.verify(country_calling_code, phone_number, sms_verification.serial_number,
                                           sms_verification.code+'1')


def test_verify_with_valid_code2():
    country_calling_code = '86'
    phone_number = '18510238421'
    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_calling_code, phone_number)
    assert False == SMSVerification.verify(country_calling_code, phone_number, sms_verification.serial_number+'1', sms_verification.code)


def test_verify_with_valid_code3():
    country_calling_code = '86'
    phone_number = '18510238421'
    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_calling_code, phone_number)
    assert False == SMSVerification.verify(country_calling_code, phone_number+'1', sms_verification.serial_number, sms_verification.code)


def test_verify_with_valid_code4():
    country_calling_code = '86'
    phone_number = '18510238421'
    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_calling_code, phone_number)
    assert False == SMSVerification.verify(country_calling_code+'1', phone_number, sms_verification.serial_number, sms_verification.code)


def test_reuse_verification(unused_and_not_expired_verification):
    sms_verification = SMSVerification.create_or_get_unused_verification_code(COUNTRY_CALLING_CODE, PHONE_NUMBER)
    assert sms_verification.code == unused_and_not_expired_verification.code
    assert sms_verification.serial_number == unused_and_not_expired_verification.serial_number
    assert sms_verification.id == unused_and_not_expired_verification.id
    assert sms_verification.expire_time != unused_and_not_expired_verification.expire_time
