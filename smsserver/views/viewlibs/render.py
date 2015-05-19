# coding: utf8
from flask import jsonify


def ok(content='', status_code=200):
    msg = {'status': 'ok', 'content': content}
    response = jsonify(msg)
    response.status_code = status_code
    return response


def error(error='', status_code=400):
    if isinstance(error, (tuple, list)):
        msg = {
            'status': 'error',
            'code': error[0],
            'msg': error[1],
        }
    else:
        msg = {
            'status': 'error',
            'msg': error,
        }

    response = jsonify(msg)
    response.status_code = status_code
    return response
