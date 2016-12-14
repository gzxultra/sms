# coding: utf-8

from smsserver.models.sms_center import SMSProvider
from smsserver.models.const import SMSProviderIdent


if __name__ == '__main__':
    SMSProvider.create(name=u'云片', ident=SMSProviderIdent.yunpian, weight=10)
    SMSProvider.create(name=u'大汉三通', ident=SMSProviderIdent.dahansantong, weight=0)
    SMSProvider.create(name=u'阿里大于', ident=SMSProviderIdent.alidayu, weight=0)
