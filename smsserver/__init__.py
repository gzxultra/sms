# coding: utf-8

from gevent import monkey
monkey.patch_all()

import logging
import logging.config
import simplejson
from os.path import join, exists, dirname
from flask import Flask
from conf import Config
from smsserver.models import db
from raven.contrib.flask import Sentry
from flask.ext.mako import MakoTemplates
from flask.ext.statsd import FlaskStatsd


def register_hooks(app):
    @app.before_request
    def _before_request():
        db.connect()

    @app.teardown_request
    def _teardown_request(exception):
        if not db.is_closed():
            db.close()


def register_route(app):
    from smsserver.views import apiv1, god
    app.register_blueprint(apiv1.bp, url_prefix='/api/v1')
    app.register_blueprint(god.bp, url_prefix='/god')


def register_logger(app):
    path = join(dirname(dirname(__file__)), 'conf', 'logging.json')
    if exists(path):
        with open(path, 'rt') as f:
            logging_config = simplejson.loads(f.read())
        logging.config.dictConfig(logging_config)
    else:
        logging.basicConfig(level=logging.INFO)


def register_sentry(app):
    if not Config.DEBUG:
        Sentry(app)


def register_mako(app):
    MakoTemplates(app)


def register_statsd(app):
    if not Config.DEBUG:
        FlaskStatsd(app=app, host=Config.STATSD_HOST, port=Config.STATSD_PORT)


app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)


register_hooks(app)
register_route(app)
register_logger(app)
register_sentry(app)
register_mako(app)
register_statsd(app)
