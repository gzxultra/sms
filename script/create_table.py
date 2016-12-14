# coding: utf-8

from smsserver.models.sms_center import SMSProvider, SMSRecord, SMSProviderServiceArea
from smsserver.models.sms_verification import SMSVerification


def main():
    SMSProvider.create_table()
    SMSRecord.create_table()
    SMSProviderServiceArea.create_table()
    SMSVerification.create_table()


if __name__ == '__main__':
    main()
