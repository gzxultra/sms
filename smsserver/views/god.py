# coding: utf8
import simplejson
import datetime
from itertools import groupby
from flask import Blueprint, g, request, abort, Response, jsonify
from flask.ext.mako import render_template
from smsserver.models.sms_center import SMSProvider, SMSRecord


__all__ = ['bp']


bp = Blueprint('god', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/interface_balance')
def interface_balance():
    providers = []
    for i in SMSProvider.where():
        providers.append({'name': i.name, 'weight': i.end-i.start, 'id': i.id})

    return render_template('interface_balance.html', sms_providers=providers)


@bp.route('/interface_balance/set', methods=['POST'])
def set_interface_balance():
    data = request.form.get('data')
    SMSProvider.reset_weight(simplejson.loads(data))
    return jsonify({})


def _sms_send_sort_by_phone_number(start_time):
    sms_list = list(SMSRecord.where('create_time > %s', start_time))
    sms_list.sort(key=lambda x: x.phone_number, reverse=True)
    l = []
    for k, b in groupby(sms_list, lambda x: x.phone_number):
        l.append((k, len(list(b))))
    return l


@bp.route('/statistics')
def statistics():
    now = datetime.datetime.now()
    data = []

    data.append(('一天内短信接口发送统计', [(i.name, SMSRecord.where('provider_id=%s and create_time > %s', i.id, now-datetime.timedelta(days=1)).count()) for i in SMSProvider.where()]))
    data.append(('一周内短信接口发送统计', [(i.name, SMSRecord.where('provider_id=%s and create_time > %s', i.id, now-datetime.timedelta(days=7)).count()) for i in SMSProvider.where()]))
    data.append(('一天内号码发送统计', _sms_send_sort_by_phone_number(now-datetime.timedelta(days=1))))
    data.append(('一周内号码发送统计', _sms_send_sort_by_phone_number(now-datetime.timedelta(days=7))))

    return render_template('statistics.html', data=data)


@bp.route('/query')
def query():
    phone_number = request.args.get('phone_number', '')

    records = SMSRecord.where(phone_number=phone_number).order_by('create_time desc')

    return render_template('query.html', records=records)
