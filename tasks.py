# coding: utf-8
import requests

import run_dev_server  # noqa
from beeprint import pp
from conf import Config
from invoke import task
from smsserver.views.viewlibs.decorator import compute_sign


def call(path, **params):
    params['public_key'] = Config.PUBLIC_KEY
    params['signature'] = compute_sign(params, secret_key=Config.SECRET_KEY)
    res = requests.post('http://127.0.0.1:8001/api/v1/{}.json'.format(path), data=params)
    return res.json()


@task
def send(ctx, phone_number, country_code='86', mode='async', send_mode='sms'):
    pp(call(
        'verification/send',
        country_code=country_code,
        phone_number=phone_number,
        mode=mode,
        send_mode=send_mode
    ))
