# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: Flask app

Copyright 2014-2021, EIO Team.
License: MIT
"""
import os
from flask import Flask, session
import logging
log = logging.getLogger('eio_userdb')

# ------------ Configuration ------------- #
app = Flask(__name__)
app.config.from_object('eio_userdb.config.Config')
SETTINGS_FILE=os.path.join(os.path.abspath(os.curdir), 'settings.py')
if os.path.exists(SETTINGS_FILE):
    log.debug('Loading settings from %s' % SETTINGS_FILE)
    app.config.from_pyfile(SETTINGS_FILE)
if 'EIO_SETTINGS' in os.environ:
    log.debug('Loading settings from %s' % os.environ['EIO_SETTINGS'])
    app.config.from_envvar('EIO_SETTINGS')

# ------------ I18N ------------- #
from flask_babel import Babel
babel = Babel(app)
@babel.localeselector
def get_locale():
        return session.get('lang', 'et')

# ------------ DB ------------- #
from .model import db
db.init_app(app)

# ------------ Mail ------------ #
from flask_mail import Mail
mail = Mail()
mail.init_app(app)

# ------------ Web ------------- #
from . import views
from . import admin

# ------------ Auto-fix proxy IP address and host ------ #
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app)

