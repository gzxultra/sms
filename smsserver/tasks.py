from celery import Celery
from conf import Config
from smsserver.models.sms_center import SMSCenter
from smsserver.models.sms_verification import SMSVerification


celery = Celery('celery', Config.CELERY_BROKER_URL)
celery.conf.update(CELERY_ACKS_LATE=True)


@celery.task
def async_send_verification_code(sms_verification_id):
    obj = SMSVerification.get(sms_verification_id)
    if not obj:
        return

    obj.send_sms()


@celery.task
def async_send_sms(country_code, phone_number, text):
    SMSCenter.send(country_code, phone_number, text)
