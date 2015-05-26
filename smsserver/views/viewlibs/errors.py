# coding: utf8


class Apiv1Error(object):
    signature_error = (1000, 'signature error')
    parameter_type_error = (1001, 'parameter type error')
    not_all_parameters_provided = (1002, 'not all parameters provided')

    invalid_verification_code = (2000, 'invalid verification code')
    send_verification_code_failed = (2001, 'send_verification_code_failed')
