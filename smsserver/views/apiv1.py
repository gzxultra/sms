# coding: utf-8
import logging
import simplejson
from flask import Blueprint
from flask import request
from smsserver.models.sms_verification import SMSVerification
from smsserver.models.sms_center import SMSSendFailed, SMSCenter
from smsserver.views.viewlibs.decorator import apiv1_signed
from smsserver.views.viewlibs.render import error, ok
from smsserver.views.viewlibs.errors import Apiv1Error
from conf import Config


__all__ = ['bp']


bp = Blueprint('apiv1', __name__)
apiv1_logger = logging.getLogger('apiv1')


@bp.route('/message/send.json', methods=['POST'])
@apiv1_signed
def send_plain_text():
    country_code = request.form.get('country_code', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    text = request.form.get('text', '').strip()

    if not all([country_code, phone_number, text]):
        apiv1_logger.error('send_plain_text,%s,%s' % (Apiv1Error.not_all_parameters_provided[0],
                                                      simplejson.dumps(request.form)))
        return error(Apiv1Error.not_all_parameters_provided)

    try:
        SMSCenter.send(country_code, phone_number, text)
    except SMSSendFailed as e:
        apiv1_logger.error('send_plain_text,%s,%s' % (e.message, simplejson.dumps(request.form)))
        return error(Apiv1Error.send_plain_text_failed)

    return ok()


@bp.route('/verification/send.json', methods=['POST'])
@apiv1_signed
def phone_send_verification_code():
    country_code = request.form.get('country_code', '').strip()
    phone_number = request.form.get('phone_number', '').strip()

    if not all([country_code, phone_number]):
        apiv1_logger.error('send_verification_code,%s,%s' % (Apiv1Error.not_all_parameters_provided[0],
                                                             simplejson.dumps(request.form)))
        return error(Apiv1Error.not_all_parameters_provided)

    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_code, phone_number)

    try:
        sms_verification.send_sms()
    except SMSSendFailed as e:
        apiv1_logger.error('send_verification_code,%s,%s,%s' % (Apiv1Error.send_verification_code_failed[0],
                                                                simplejson.dumps(request.form), e.message))

        return error(Apiv1Error.send_verification_code_failed)

    return ok({'serial_number': sms_verification.serial_number,
               'country_code': country_code,
               'phone_number': phone_number})


@bp.route('/verification/verify.json', methods=['POST'])
@apiv1_signed
def verify_code():
    country_code = request.form.get('country_code', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    code = request.form.get('code', '').strip()

    if not all([country_code, phone_number, code]):
        apiv1_logger.error('verify_code,%s,%s' % (Apiv1Error.not_all_parameters_provided[0],
                                                  simplejson.dumps(request.form)))

        return error(Apiv1Error.not_all_parameters_provided)

    # 测试服务器万能验证码
    if Config.DEBUG and code == '000000':
        return ok()

    if not SMSVerification.verify(country_code, phone_number, code):
        apiv1_logger.error('verify_code,%s,%s' % (Apiv1Error.invalid_verification_code[0],
                                                  simplejson.dumps(request.form)))
        return error(Apiv1Error.invalid_verification_code)
    return ok()
