# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: "Business logic"

Copyright 2014, EIO Team.
License: MIT
"""
from time import time
from datetime import datetime
import traceback

from flask import request, Markup, flash, redirect, url_for
from flask_mail import Message
from flask.ext.babel import gettext
from sqlalchemy import or_

from .main import app, db, mail
from .model import User, Participation, UserInfo
from .cmscommon.crypto import hash_password

import hashlib

def getstr():
    return gettext('Kool/asutus')

def send_activation_email(u):
    if u.password.startswith('~plaintext:'):
        password = u.password[11:]
    elif u.password.startswith('plaintext:'):
        password = u.password[10:]
    else:
        password = None
    options = {'activation_code': u.user_info.activation_code(int(time()/60)),
               'registration_server_url': app.config['REGISTRATION_SERVER_URL'],
               'contest_server_url': app.config['CONTEST_SERVER_URL'],
               'username': u.username,
               'password': password,
               'email': u.email}
    
    msg = Message(recipients=[u.email],
                  subject=app.config['REGISTRATION_EMAIL_SUBJECT'],
                  body=app.config['REGISTRATION_EMAIL_BODY'] % options)
    if app.config['MAIL_DEBUG']:
        print msg
    mail.send(msg)


def register(form):
    try:
        # Check whether the user with the same email is already registered for the same contest_id
        existing_user = (db.session.query(User).join(Participation)
                        .filter(Participation.contest_id == app.config['CONTEST_ID'])
                        .filter(User.email == form.email.data)).first()
        if existing_user:
            if existing_user.password.startswith('~'): # Not activated
                send_activation_email(existing_user)
                flash(Markup(gettext(u"Sellise aadressiga kasutaja on juba registreeritud ja aktiveerimikood saadetud. " + \
                        u"Kasutaja andmete muutmiseks võtke ühendust <a href='mailto:eio-support@lists.ut.ee'>administraatoriga</a>.")), "danger")
                return redirect(url_for('activate'))
            else:
                flash(Markup(gettext(u"Sellise aadressiga kasutaja on juba registreeritud. Parooli vahetada saate <a href='%(url)s'>siit</a>. Muude andmete muutmiseks võtke ühendust <a href='mailto:eio-support@lists.ut.ee'>administraatoriga</a>.", url=url_for('passwordreset'))), "danger")
                return None

        # No, the user is not yet registered for the contest (and we know no other user has the same username from the form validation check).
        # We first erase any users with the same username or email from the database:
        for u in db.session.query(User).filter(or_(
                        User.email == form.email.data,
                        User.username == form.username.data)).all():
            db.session.delete(u)  # Note that we delete one by one. This way SQLAlchemy will cascade to UserInfo correctly.
        db.session.commit()

        # Now add a non-activated user to the database, register a participation, and send activation email
        p = hashlib.sha256(app.config['MAGIC'] + str(time) + form.username.data).hexdigest()[:10]
        u = User(first_name=form.first_name.data,
                 last_name=form.last_name.data,
                 username=form.username.data,
                 password='~' + hash_password(p, method='plaintext'),  # For unactivated users we prepend ~ to the password field
                 email=form.email.data)
        ui = UserInfo(category=form.category.data,
                      school=form.school.data,
                      grade=form.grade.data,
                      code_lang=form.code_lang.data,
                      text_lang=form.text_lang.data,
                      registration_time=datetime.now(),
                      registration_ip=request.remote_addr)
        u.user_info = ui
        u.participations.append(Participation(contest_id=app.config['CONTEST_ID'], user=u))
        db.session.add(u)

        db.session.commit()
        send_activation_email(u)
        flash(gettext(u"Kasutaja emailile saadeti kiri aktiveerimiskoodiga (kontrollige ka spämmikausta, eriti GMaili kasutajad!), palun sisestage kood alltoodud tekstivälja."), 'success')
        return redirect(url_for('activate'))
    except Exception, e:
        traceback.print_exc()            
        flash(e.message, 'danger')


def is_valid_activation(code, expiration_minutes):
    try:
        a, b, c = str(code).split('$')
        r = db.session.query(UserInfo).get(int(b))
        cur_time = int(time()/60)
        for i in range(0, expiration_minutes):
            if r.activation_code(cur_time - i) == code:
                return True
    except:
        traceback.print_exc()
        return False
    return False


def activate(code):
    if is_valid_activation(code, 60*20):
        u = db.session.query(User).get(int(code.split('$')[1]))
        if u.password.startswith('~'):
            u.password = u.password[1:]
            db.session.commit()
        return True
    else:
        return False


def reset_password(code, new_password):
    if is_valid_activation(code, 30):
        u = db.session.query(User).get(int(code.split('$')[1]))
        if u.password.startswith('~'):
            flash(gettext("Kasutaja pole aktiveeritud"), "danger")
        else:
            u.password = hash_password(new_password, method='plaintext')
            db.session.commit()
            flash(gettext("Parool vahetatud"), "success")
            return redirect(url_for("blank"))
    else:
        flash(gettext(u"Vale või aegunud autentimiskood"), "danger")


def send_password_reset_mail(email):
    u = db.session.query(User).join(Participation).filter(Participation.contest_id == app.config['CONTEST_ID'],
                                                    User.email == email).first()
    if not u:
        flash(gettext("Sellise emailiga kasutaja pole registreeritud"), "danger")
        return
    else:
        options = {'activation_code': u.user_info.activation_code(int(time()/60)),
                   'registration_server_url': app.config['REGISTRATION_SERVER_URL'],
                   'username': u.username}
        
        msg = Message(recipients=[u.email],
                      subject=gettext("Parooli vahetamine"),
                      body=gettext(u"""Keegi (arvatavasti Teie ise) soovis vahetada Teie EIO kasutaja parooli.
                      
Parooli saate vahetada lehel %(registration_server_url)spasswordreset/%(activation_code)s
järgmise poole tunni jooksul. Teie kasutajatunnus on %(username)s.

Kui Te ise paroolivahetust ei tellinud, ignoreerige seda kirja.

Lugupidamisega,
Veebiserver
    """) % options)
        if app.config['MAIL_DEBUG']:
            print msg
        mail.send(msg)
        flash(gettext("Paroolivahetuse juhendid saadetud etteantud aadressile"), "success")
        return redirect(url_for('blank'))

