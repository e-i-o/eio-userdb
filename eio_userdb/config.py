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
    
    # App settings

    # Key for password / activation code generation
    SECRET_KEY = '1aed126482fa0d7ea99c8b54b5198df4'
    # Password for the admin UI
    SECRET_PASSWORD = 's3cr3t'
    CONTEST_ID = 1
    # Registration page title
    CONTEST_TITLE = 'Eesti Informaatikaolümpiaad'
    # 'open' or 'basic' - controls whether to show division selector when registering
    CONTEST_TYPE = 'basic'
    # email that's shown for support requests
    SUPPORT_EMAIL = 'eio@eio.ee'
    REGISTRATION_SERVER_URL = 'http://localhost:5000/'
    CONTEST_SERVER_URL = 'http://eio-contest.us.to/'
    RANKING_SERVER_URL = 'http://usern4me:passw0rd@localhost:33382/'
    
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
    # log all mails that would be sent to stdout
    MAIL_DEBUG = False

    # Should not be changed
    # Enable string translation in forms    
    WTF_I18N_ENABLED = True
    # Silence flask-sqlalchemy warnings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
