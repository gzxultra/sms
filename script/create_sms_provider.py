# coding: utf8

from smsserver.models.sms_center import SMSProvider
from smsserver.models.const import SMSProviderIdent


if __name__ == '__main__':
    SMSProvider.create('云片', SMSProviderIdent.yunpian, 20)
