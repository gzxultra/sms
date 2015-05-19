# coding: utf8

import logging
import logging.config
import os
import sys
import simplejson
from flask import Flask
from conf import Config
from smsserver.models import db, mc
from raven.contrib.flask import Sentry
from flask.ext.mako import MakoTemplates


def register_hooks(app):
    @app.before_request
    def _before_request():
        mc.reset()

    @app.teardown_request
    def _teardown_request(exception):
        sys.stdout.flush()
        db.commit()


def register_route(app):
    from smsserver.views import apiv1, god
    app.register_blueprint(apiv1.bp, url_prefix='/api/v1')
    app.register_blueprint(god.bp, url_prefix='/god')


def register_logger(app):
    path = os.path.join(os.path.dirname(__file__), 'logging.json')
    if os.path.exists(path):
        with open(path, 'rt') as f:
            logging_config = simplejson.loads(f.read())
        logging.config.dictConfig(logging_config)
    else:
        logging.basicConfig(level=logging.INFO)


def register_sentry(app):
    if not Config.DEBUG:
        sentry = Sentry(app)


def register_mako(app):
    mako = MakoTemplates(app)


app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)


register_hooks(app)
register_route(app)
register_logger(app)
register_sentry(app)
register_mako(app)
