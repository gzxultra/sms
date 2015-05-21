# coding: utf8
import logging
from flask import Blueprint
from flask import request
from smsserver.models.sms_verification import SMSVerification
from smsserver.models.sms_center import SMSSendFailed
from smsserver.views.viewlibs.decorator import apiv1_signed
from smsserver.views.viewlibs.render import error, ok
from smsserver.views.viewlibs.errors import Apiv1Error
from conf import Config


__all__ = ['bp']


bp = Blueprint('apiv1', __name__)
apiv1_logger = logging.getLogger('apiv1')


@bp.route('/verification/send.json', methods=['POST'])
@apiv1_signed
def phone_send_verification_code():
    country_code = request.form.get('country_code', '').strip()
    phone_number = request.form.get('phone_number', '').strip()

    if not all([country_code, phone_number]):
        return error(Apiv1Error.not_all_parameters_provided)

    sms_verification = SMSVerification.create_or_get_unused_verification_code(country_code, phone_number)
    sms_verification.send_sms()

    return ok({'serial_number': sms_verification.serial_number,
               'country_code': country_code,
               'phone_number': phone_number})


@bp.route('/verification/verify.json', methods=['POST'])
@apiv1_signed
def verify_code():
    country_code = request.form.get('country_code', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    serial_number = request.form.get('serial_number', '').strip()
    code = request.form.get('code', '').strip()

    if not all([country_code, phone_number, serial_number, code]):
        return error(Apiv1Error.not_all_parameters_provided)

    # 测试服务器万能验证码
    if Config.DEBUG and serial_number == 'superserialnumber' and code == 'supercode':
        return ok()

    ret = SMSVerification.verify(country_code, phone_number, serial_number, code)
    if ret:
        return ok()

    return error(Apiv1Error.invalid_verification_code)
