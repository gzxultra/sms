# coding: utf-8
import simplejson
import datetime
from itertools import groupby
from flask import Blueprint, request, jsonify
from flask.ext.mako import render_template
from smsserver.models.sms_center import SMSProvider, SMSRecord
from smsserver.models.const import SMSSendStatus


__all__ = ['bp']


bp = Blueprint('god', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/interface_balance')
def interface_balance():
    providers = []
    for i in SMSProvider.select():
        providers.append({'name': i.name, 'weight': i.weight, 'id': i.id})

    return render_template('interface_balance.html', sms_providers=providers)


@bp.route('/interface_balance/set', methods=['POST'])
def set_interface_balance():
    data = request.form.get('data')
    for pid, weight in simplejson.loads(data).iteritems():
        provider = SMSProvider.get(id=pid)
        provider.set_weight(weight)

    return jsonify({})


def _sms_send_sort_by_phone_number(start_time):
    sms_recors = SMSRecord.select().where((SMSRecord.status == SMSSendStatus.success) &
                                          (SMSRecord.create_time > start_time)).order_by(SMSRecord.phone_number)
    l = []
    for k, b in groupby(sms_recors, lambda x: x.phone_number):
        record_num = len(list(b))
        if record_num >= 2:
            l.append((k, record_num))
    l.sort(key=lambda x: x[1], reverse=True)
    return l


def _sms_send_status_by_provider(start_time, provider):
    success_num = SMSRecord.select().where((SMSRecord.status == SMSSendStatus.success) &
                                          (SMSRecord.provider_id == provider.id) &
                                          (SMSRecord.create_time > start_time)).count()

    total = SMSRecord.select().where((SMSRecord.status == SMSSendStatus.success) &
                                     (SMSRecord.create_time > start_time)).count()
    return '%s / %s' % (success_num, total)


@bp.route('/statistics')
def statistics():
    now = datetime.datetime.now()
    data = []

    one_day_before = now - datetime.timedelta(days=1)
    one_week_before = now - datetime.timedelta(days=7)

    providers = SMSProvider.select()

    data.append((u'一天内短信接口发送统计(成功/总数)', [(i.name, _sms_send_status_by_provider(one_day_before, i)) for i in providers]))
    data.append((u'一周内短信接口发送统计(成功/总数)', [(i.name, _sms_send_status_by_provider(one_week_before, i)) for i in providers]))
    data.append((u'一天内号码发送统计', _sms_send_sort_by_phone_number(one_day_before)))
    data.append((u'一周内号码发送统计', _sms_send_sort_by_phone_number(one_week_before)))

    return render_template('statistics.html', data=data)


@bp.route('/query')
def query():
    phone_number = request.args.get('phone_number', '')
    records = SMSRecord.select().where(SMSRecord.phone_number == phone_number).order_by(SMSRecord.create_time.desc())
    return render_template('query.html', records=records)
