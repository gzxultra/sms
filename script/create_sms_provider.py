# coding: utf8

from smsserver.models.sms_center import SMSProvider


if __name__ == '__main__':
    SMSProvider.create(name='云片', start=0, end=100)
