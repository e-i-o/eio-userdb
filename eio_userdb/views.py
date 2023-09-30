# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: Flask views.

Copyright 2014-2021, EIO Team.
License: MIT
"""
from datetime import datetime
import traceback

from flask import render_template, flash, Markup, request, session, redirect, url_for, jsonify, make_response
from flask_wtf import FlaskForm as Form
from wtforms import StringField, SelectField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError
from flask_mail import Message
from flask_babel import lazy_gettext, gettext
from sqlalchemy import or_

from .main import app, mail
from .model import db, User, Participation
from . import logic

import logging
log = logging.getLogger('eio_userdb.views')

# ---------------------------------------------------------------------------- #
@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang not in ['et', 'en']:
        if 'lang' in session:
            del session['lang']
    else:
        session['lang'] = lang
    return redirect(request.args.get('prev', url_for('index')))


@app.route('/blank')
def blank():
    return render_template('base.html')

@app.route('/over')
def over():
    return render_template('over.html')

# ---------------------------------------------------------------------------- #
class RegistrationForm(Form):
    first_name = StringField(lazy_gettext('Eesnimi'), validators=[DataRequired(), Length(max=255)])
    last_name = StringField(lazy_gettext('Perenimi'), validators=[DataRequired(), Length(max=255)])

    # lahtine võistlus
    category = SelectField(lazy_gettext('Kategooria'), validators=[DataRequired()],
        choices=[('', ''),
            ('est-sch', lazy_gettext(u'Eesti õpilane')), ('est-uni', lazy_gettext(u'Eesti üliõpilane')),
            ('for-sch', lazy_gettext(u'Muu õpilane')), ('for-uni', lazy_gettext(u'Muu üliõpilane')), 
            ('other', lazy_gettext('Muu'))])
    school = StringField(lazy_gettext('Kool/asutus'), validators=[DataRequired(), Length(max=255)],
        description=lazy_gettext(u'(Eesti kooli või ülikooli korral ametlik nimi eesti keeles)'))
    grade = StringField(lazy_gettext('Klass'), validators=[DataRequired(), Length(max=255)],
        description=lazy_gettext(u'(Õpilastel 1..12, üliõpilastel I..V, muudel "-")'))

    # eelvoor
    #category = HiddenField('')
    #category = SelectField(lazy_gettext(u'Rühm'), validators=[DataRequired()],
    #    choices=[('', ''), ('P', lazy_gettext(u'Põhikool')), ('G', lazy_gettext(u'Gümnaasium'))])
    #category = SelectField(lazy_gettext(u'Rühm'), validators=[DataRequired()],
    #    choices=[('', ''), ('P', lazy_gettext(u'Põhikool')), ('G', lazy_gettext(u'Gümnaasium')), ('E', lazy_gettext(u'Edasijõudnud'))])
    #school = StringField(lazy_gettext('Kool'), validators=[DataRequired(), Length(max=255)],
    #    description=lazy_gettext(u'(Kooli ametlik nimi eesti keeles)'))
    #grade = StringField(lazy_gettext('Klass'), validators=[DataRequired(), Length(max=255)],
    #    description=u'(1..12)')

    email = StringField(lazy_gettext('Meiliaadress'), validators=[DataRequired(), Email(), Length(max=120)])
    
    code_lang = StringField(lazy_gettext(u'Programmeerimiskeel'), validators=[DataRequired(), Length(max=120)],
        description=lazy_gettext(u'(Pole garanteeritud, et kõiki soovitud keeli kasutada saab)'))
    text_lang = SelectField(lazy_gettext(u'Ülesannete keel'),
        choices=[('ee', 'Eesti'), ('en', 'English')])

    spacer = HiddenField('')

    username = StringField(lazy_gettext('Kasutajatunnus'), validators=[DataRequired(),
            Regexp('^[A-Za-z0-9]+$', message=lazy_gettext(u'Kasutajatunnus peab koosnema tähtedest ja numbritest')),
            Length(min=2, message=lazy_gettext(u'Kasutajatunnus liiga lühike')),
            Length(max=10, message=lazy_gettext(u'Kasutajatunnus liiga pikk'))],
        description=lazy_gettext(u'Valige kasutajatunnus süsteemi sisse logimiseks'))

    #password = PasswordField(lazy_gettext('Parool'), validators=[DataRequired(),
    #        Length(min=4, message=lazy_gettext(u'Parool liiga lühike')), Length(max=100),
    #        EqualTo('confirm', message=lazy_gettext(u'Parool ja parooli kordus ei ole identsed'))])
    #confirm = PasswordField(lazy_gettext('Parooli kordus'))

    agree = BooleanField(lazy_gettext(u'Olen nõus, et minu andmeid kasutatakse informaatikavõistlustega seotud teavitusteks'),
        validators=[DataRequired(message=lazy_gettext(u'Puudub nõusolek andmete kasutamiseks'))])

    def validate_username(form, field):
        """Disallow usernames which are already present in the contest but associated with a different email"""
        if (db.session.query(User).join(Participation)
                .filter(Participation.contest_id == app.config['CONTEST_ID'])
                .filter(or_(User.email == None, User.email != form.email.data))
                .filter(User.username == field.data)).count():
            raise ValidationError(lazy_gettext("Kasutajatunnus on juba kasutusel"))

@app.route('/register', methods=('GET', 'POST'))
def register():
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        result = logic.register(form)
        if result is not None:
            return result
    return render_template('register.html', form=form)

# ---------------------------------------------------------------------------- #
class ActivateForm(Form):
    code = StringField(lazy_gettext('Aktiveerimiskood'), validators=[DataRequired(), Length(max=120)])

@app.route('/activate', methods=('GET', 'POST'))
def activate():
    form = ActivateForm(request.args if request.method == 'GET' else request.form, csrf_enabled=False)
    if 'code' in request.args and form.validate():
        if logic.activate(form.code.data.strip()):
            flash(Markup(gettext(u'Kasutaja aktiveeritud.')), 'success')
            return redirect(url_for('blank'))
        else:
            flash(gettext(u'Vale või aegunud aktiveerimiskood.'), 'danger')
    return render_template('activate.html', form=form)

# ---------------------------------------------------------------------------- #
class PasswordForm(Form):
    password = PasswordField(lazy_gettext('Uus parool'), validators=[DataRequired(),
            Length(min=4, message=lazy_gettext(u'Parool liiga lühike')), Length(max=100),
            EqualTo('confirm', message=lazy_gettext(u'Parool ja parooli kordus ei ole identsed'))])
    confirm = PasswordField(lazy_gettext('Parooli kordus'))

class EmailForm(Form):
    email = StringField(lazy_gettext('Meiliaadress'), validators=[DataRequired(), Email(), Length(max=120)])

@app.route('/passwordreset', methods=('GET', 'POST'))
@app.route('/passwordreset/<code>', methods=('GET', 'POST'))
def passwordreset(code=None):
    password_form = PasswordForm(request.form)
    email_form = EmailForm(request.form)
    if code is not None:
        if password_form.validate_on_submit():
            r = logic.reset_password(code, password_form.password.data)
            if r is not None:
                return r
    elif email_form.validate_on_submit():
        r = logic.send_password_reset_mail(email_form.email.data)
        if r is not None:
            return r
    return render_template('passwordreset.html', code=code, password_form=password_form, email_form=email_form)

# ---------------------------------------------------------------------------- #
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
