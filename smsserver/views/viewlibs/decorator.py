# coding: utf8
import hashlib
from operator import itemgetter
from decimal import Decimal
from functools import wraps
from flask import request
from smsserver.views.viewlibs.render import error
from smsserver.views.viewlibs.errors import Apiv1Error
from conf import Config


def compute_sign(d, secret_key):
    md5_str = ''

    for key, value in sorted(d.items(), key=itemgetter(0)):
        if isinstance(value, unicode):
            value = value.encode('utf8')
        if isinstance(value, str):
            md5_str += "%s%s" % (key, value)
        if isinstance(value, Decimal):
            md5_str += "%s%s" % (key, value)
    md5_str += str(secret_key)
    api_sign = hashlib.md5(md5_str).hexdigest()
    return api_sign


def verify_sign(d):
    sign_val = d.pop('signature', None)
    public_key = d.get('public_key')
    secret_key = Config.SECRET_KEY
    if public_key == Config.PUBLIC_KEY and sign_val == compute_sign(d, secret_key=secret_key):
        return True
    return False


def apiv1_signed(func):
    @wraps(func)
    def _signed(*args, **kwargs):
        d = {}
        if request.method == 'POST':
            for k, v in request.form.iteritems():
                d[k] = v
        elif request.method == 'GET':
            for k, v in request.args.iteritems():
                d[k] = v

        if verify_sign(d):
            return func(*args, **kwargs)
        return error(Apiv1Error.signature_error, 401)
    return _signed
