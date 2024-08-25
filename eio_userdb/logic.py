# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: "Business logic"

Copyright 2014-2021, EIO Team.
License: MIT
"""
from time import time
from datetime import datetime
import traceback

from flask import request, Markup, flash, redirect, url_for
from flask_mail import Message
from flask_babel import gettext

from .main import app, db, mail
from .model import User, Participation, UserInfo
from .cmscommon.crypto import hash_password

import hmac
import requests
from requests.exceptions import RequestException
import string

import logging
log = logging.getLogger('eio_userdb.logic')

def generate_password(username):
    key = app.config['SECRET_KEY'].encode()
    message = ("password|" + str(time()) + "|" + username).encode()
    return hmac.new(key, message, 'sha256').hexdigest()[:10]

def build_activation_code(user, salt=None):
    if salt is None:
        salt = int(time() / 60)
    key = app.config['SECRET_KEY'].encode()
    message = ('code|' + user.email + '|' + user.password + '|' + str(salt)).encode()
    # hmac-sha256 has a 32-byte output, which is a bit long when hex-encoded. 16 bytes is fine for this use case
    mac = hmac.digest(key, message, 'sha256')[:16]
    return f'{user.id}z{mac.hex()}'

def user_id_from_code(code: str):
    l = code.split('z')
    if len(l) == 0 or not l[0].isdigit():
        return None
    return int(l[0])

def is_valid_activation(code, expiration_minutes):
    try:
        r = db.session.query(UserInfo).get(user_id_from_code(code))
        user = r.user
        cur_time = int(time() / 60)
        for i in range(0, expiration_minutes):
            if build_activation_code(user, cur_time - i) == code:
                return True
    except:
        traceback.print_exc()
        return False
    return False

def encode_id(entity_id):
    """Encode the id using only A-Za-z0-9_.

    entity_id (unicode): the entity id to encode.
    return (unicode): encoded entity id.

    """
    encoded_id = ""
    for char in entity_id:
        if char not in string.ascii_letters + string.digits:
            encoded_id += "_%x" % ord(char)
        else:
            encoded_id += char
    return encoded_id

def send_activation_email(u):
    if u.password.startswith('~plaintext:'):
        password = u.password[11:]
    elif u.password.startswith('plaintext:'):
        password = u.password[10:]
    else:
        password = None
    options = {'activation_code': build_activation_code(u),
               'registration_server_url': app.config['REGISTRATION_SERVER_URL'],
               'contest_server_url': app.config['CONTEST_SERVER_URL'],
               'username': u.username,
               'password': password,
               'email': u.email}
    
    msg = Message(recipients=[u.email],
                  subject=gettext("Registreerimise kinnitus"),
                  body=gettext(
"""Olete registreerunud EIO lahenduste esitamise süsteemi kasutajaks.

Oma konto aktiveerimiseks sisestage järgneva 20 tunni jooksul kood
%(activation_code)s lehel %(registration_server_url)sactivate

Kui see on tehtud, saate serverisse sisse logida lehel
%(contest_server_url)s
kasutajatunnusega %(username)s ning parooliga %(password)s.

Pange tähele, et kasutajatunnus ja parool on tõstutundlikud!

Lugupidamisega
Veebiserver""") % options)
    if app.config['MAIL_DEBUG']:
        log.debug(msg)
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
                flash(Markup(gettext("Sellise meiliaadressiga kasutaja on juba registreeritud ja aktiveerimikood saadetud. " + \
                    "Kasutaja andmete muutmiseks võtke ühendust <a href='mailto:%(support_email)s'>administraatoriga</a>.",
                        support_email=app.config['SUPPORT_EMAIL'])), "danger")
                return redirect(url_for('activate'))
            else:
                flash(Markup(gettext("Sellise meiliaadressiga kasutaja on juba registreeritud. " + \
                    "Parooli vahetada saate <a href='%(url)s'>siit</a>. " + \
                    "Muude andmete muutmiseks võtke ühendust <a href='mailto:%(support_email)s'>administraatoriga</a>.",
                        url=url_for('passwordreset'), support_email=app.config['SUPPORT_EMAIL'])), "danger")
                return None

        for u in db.session.query(User).filter(User.username == form.username.data).all():
            # this username is used already for a previous contest, so rename it.
            # we really shouldn't have users with 0 participations, but let's handle it just in case.
            if len(u.participations) == 0:
                new_name = "contestX_" + u.username
            else:
                contest_id = u.participations[0].contest_id
                new_name = f"contest{contest_id}_{u.username}"
            u.username = new_name
        db.session.commit()

        # No, the user is not yet registered for the contest (and we know no other user has the same username from the form validation check).

        # Now add a non-activated user to the database, register a participation, and send activation email
        p = generate_password(form.username.data)
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
        part = Participation(contest_id=app.config['CONTEST_ID'],
                             division=form.category.data,
                             user=u,
                             hidden=True)
        u.participations.append(part)
        db.session.add(u)

        db.session.commit()
        send_activation_email(u)
        flash(gettext("Aktiveerimiskood saadetud meiliga, palun sisestage see allolevasse tekstivälja. "
            "Kontrollige kindlasti ka spämmikausta, eriti GMaili kasutajad! "
            "Kui kood mõne minuti jooksul kohale ei jõua, andke sellest teada aadressil %(support_email)s.",
                      support_email=app.config['SUPPORT_EMAIL']), 'success')
        return redirect(url_for('activate'))
    except Exception as e:
        traceback.print_exc()            
        flash(str(e), 'danger')

def activate(code):
    if is_valid_activation(code, 60*20):
        u = db.session.query(User).get(user_id_from_code(code))
        if u.password.startswith('~'):
            u.password = u.password[1:]
            for p in u.participations:
                p.hidden = False
            db.session.commit()

            # Inform RWS that a new user has been added
            for p in u.participations:
                if p.contest_id == app.config['CONTEST_ID']:
                    try:
                        team = p.team
                        r = requests.put(app.config['RANKING_SERVER_URL'] + "users/", json={
                            encode_id(u.username): {
                                "f_name": u.first_name,
                                "l_name": u.last_name,
                                "team": encode_id(team.code)
                                        if team is not None else None,
                                "division": p.division,
                            }
                        })
                        r.raise_for_status()
                    except RequestException as e:
                        log.warning("Could not update RWS", e)
        flash(Markup(gettext(u'Kasutaja aktiveeritud. Saate sellega sisse logida aadressil <a href="%(url)s">%(url)s</a>.',
                             url=app.config['CONTEST_SERVER_URL'])), 'success')
        return redirect(url_for('blank'))
    else:
        flash(gettext(u'Vale või aegunud aktiveerimiskood.'), 'danger')

def reset_password(code):
    if is_valid_activation(code, 30):
        u = db.session.query(User).get(user_id_from_code(code))
        if u.password.startswith('~'):
            flash(Markup(gettext("Kasutaja pole aktiveeritud. "
                "Kui te pole aktiveerimismeili saanud, võtke ühendust "
                "<a href='mailto:%(support_email)s'>administraatoriga</a>.",
                                 support_email=app.config['SUPPORT_EMAIL'])), "danger")
        else:
            p = generate_password(u.username)
            u.password = hash_password(p, method='plaintext')
            db.session.commit()
            options = {"username": u.username, "password": p}
            msg = Message(recipients=[u.email],
                          subject=gettext("Parooli vahetuse kinnitus"),
                          body=gettext(
"""Teie EIO kasutaja parool on vahetatud.

Teie kasutajanimi on %(username)s, uus parool on %(password)s.

Lugupidamisega
Veebiserver""") % options)
            if app.config['MAIL_DEBUG']:
                log.debug(msg)
            mail.send(msg)
            flash(gettext("Parool vahetatud ja uus parool meiliga saadetud"), "success")
            return redirect(url_for("blank"))
    else:
        flash(gettext("Vale või aegunud autentimiskood"), "danger")


def send_password_reset_mail(email):
    u = (db.session.query(User)
         .join(Participation)
         .filter(Participation.contest_id == app.config['CONTEST_ID'],
                 User.email == email)
         .first())
    if not u:
        flash(gettext("Sellise meiliaadressiga kasutajat pole registreeritud"), "danger")
        return
    elif u.password.startswith('~'):
        flash(Markup(gettext("Kasutaja pole aktiveeritud. "
            "Kui te pole aktiveerimismeili saanud, võtke ühendust "
            "<a href='mailto:%(support_email)s'>administraatoriga</a>.",
                             support_email=app.config['SUPPORT_EMAIL'])), "danger")
        return
    else:
        options = {'activation_code': build_activation_code(u),
                   'registration_server_url': app.config['REGISTRATION_SERVER_URL'],
                   'username': u.username}
        
        msg = Message(recipients=[u.email],
                      subject=gettext("Parooli vahetamine"),
                      body=gettext(
"""Keegi (arvatavasti Teie ise) soovis vahetada Teie EIO kasutaja parooli.

Parooli saate vahetada lehel
%(registration_server_url)spasswordreset/%(activation_code)s
järgmise poole tunni jooksul. Teie kasutajatunnus on %(username)s.

Kui Te ise paroolivahetust ei tellinud, ignoreerige seda kirja.""") % options)
        if app.config['MAIL_DEBUG']:
            log.debug(msg)
        mail.send(msg)
        flash(gettext("Paroolivahetuse juhend saadetud meiliga"), "success")
        return redirect(url_for('blank'))
