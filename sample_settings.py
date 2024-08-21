# -*- coding: utf-8 -*-

# Development settings
DEBUG = True
SQLALCHEMY_ECHO = True
MAIL_SUPPRESS_SEND = False

# App settings
SECRET_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
SECRET_PASSWORD = 's3cr3t-p4ssw0rd'
CONTEST_ID = 1
CONTEST_TITLE = u'Eesti Informaatika Olümpiaadi Eelvoor'
REGISTRATION_SERVER_URL = 'http://localhost:5000/'
CONTEST_SERVER_URL = 'http://localhost/'
RANKING_SERVER_URL = 'http://usern4me:passw0rd@localhost:33382/'
CONTACT_URL = 'http://eio.ut.ee/'
MAGIC = 'magic' # seed for user password generatio, CHANGE THIS!

import os
# Database connection
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db.sqlite')

# Deployment option
APPLICATION_ROOT = '/'  # Untested
DEBUG_SERVER_HOST = '0.0.0.0'
DEBUG_SERVER_PORT = 33300

# Flask-mail config
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = 'Eesti Informaatikaolümpiaadide server <eio@eio.ee>'
MAIL_SUPPRESS_SEND = True
MAIL_DEBUG = True

REGISTRATION_EMAIL_SUBJECT = "Registreerimise kinnitus"
REGISTRATION_EMAIL_BODY = u"""Olete registreerunud EIO lahenduste esitamise süsteemi kasutajaks.

Oma konto aktiveerimiseks sisestage järgneva 20 tunni jooksul kood
%(activation_code)s lehel %(registration_server_url)sactivate.

Kui see on tehtud, saate võistluse alates serverisse sisse logida lehel
%(contest_server_url)s,
kasutades kasutajatunnust %(username)s ning parooli %(password)s.

Pange tähele, et kasutajatunnus ja parool on tõstutundlikud.

Lugupidamisega,
Veebiserver
"""

