# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: Configuration

Copyright 2014, EIO Team.
License: MIT
"""
import os

class Config(object):
    # Development settings
    DEBUG = False
    SQLALCHEMY_ECHO = True
    MAIL_SUPPRESS_SEND = False
    
    # App settings
    SECRET_KEY = '\xf5\xfd\x94\x90\x9d\xd6;{\xb5l-}^(\xfc?\xbdW\xc6\t'
    SECRET_PASSWORD = 's3cr3t'
    CONTEST_ID = 1
    CONTEST_TITLE = u'Eesti Informaatikaolümpiaad'
    REGISTRATION_SERVER_URL = 'http://localhost:5000/'
    CONTEST_SERVER_URL = 'http://eio-contest.us.to/'
    CONTACT_URL = 'http://eio.ut.ee/'
    MAGIC = 'magic' # seed for user password generatio
    
    # Database connection
    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db.sqlite')
    
    # Deployment option
    APPLICATION_ROOT = '/'  # Untested
    DEBUG_SERVER_HOST = '0.0.0.0'
    DEBUG_SERVER_PORT = 5000
    
    # Flask-mail config
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25 
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'Eesti Informaatikaolümpiaadide server <eio@eio.ee>'
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = False

    REGISTRATION_EMAIL_SUBJECT = "Registreerimise kinnitus"
    REGISTRATION_EMAIL_BODY = u"""Olete registreerunud EIO lahenduste esitamise süsteemi kasutajaks.

Oma konto aktiveerimiseks sisestage järgneva 20 tunni jooksul kood
%(activation_code)s lehel %(registration_server_url)sactivate.

Kui see on tehtud, saate võistluse alates serverisse sisse logida lehel
%(contest_server_url)s,
kasutades kasutajatunnust %(username)s ning parooli %(password)s.

Pange tähele, et kasutajatunnus ja parool on tõstutundlikud.
"""
    
    # Should not be changed
    # Enable string translation in forms    
    WTF_I18N_ENABLED = True
