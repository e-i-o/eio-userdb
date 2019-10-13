# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: Flask views.

Copyright 2014, EIO Team.
License: MIT
"""
from datetime import datetime
import traceback

from flask import render_template, flash, Markup, request, session, redirect, url_for, jsonify, make_response
from flask_wtf import Form
from wtforms import StringField, SelectField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError
from flask_mail import Message
from flask.ext.babel import lazy_gettext
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
    #category = SelectField(lazy_gettext(u'Rühm'), choices=[('', ''), ('poh', lazy_gettext(u'Põhikool')), ('gym', lazy_gettext(u'Gümnaasium')), ('eda', lazy_gettext(u'Edasijõudnud'))], validators=[DataRequired()])
    #category = SelectField(lazy_gettext('Kategooria'), choices=[('', ''), ('school', lazy_gettext(u'õpilane')), ('university', lazy_gettext(u'üliõpilane')), ('other', lazy_gettext('muu'))], validators=[DataRequired()])
    category = HiddenField('')
    #school = StringField(lazy_gettext('Kool'), validators=[DataRequired(), Length(max=255)], description=lazy_gettext(u'(kooli ametlik nimi eesti keeles)'))
    school = StringField(lazy_gettext('Kool/asutus'), validators=[DataRequired(), Length(max=255)], description=lazy_gettext(u'(kooli korral kindlasti ametlik nimi eesti keeles, muidu ülikooli nimi või "muu")'))
    #grade = StringField(lazy_gettext('Klass'), validators=[DataRequired(), Length(max=255)], description=u'(1..12)')
    grade = StringField(lazy_gettext('Klass'), validators=[DataRequired(), Length(max=255)], description=lazy_gettext(u'(õpilastel 1..12, üliõpilastel I..V, muudel -)'))
    email = StringField(lazy_gettext('Meiliaadress'), validators=[DataRequired(), Email(), Length(max=120)])
    
    # New since 09.2019
    code_lang = StringField(lazy_gettext(u'Eelistatud programmeerimiskeel/ töökeskkond/ opsüsteem'), validators=[DataRequired(), Length(max=120)],
                            description=lazy_gettext(u'(pole garanteeritud et soovitud tööriistu või keeli kasutada saab)'))
    # New since 09.2019
    text_lang = SelectField(lazy_gettext(u'Eelistatud ülesannete keel'), choices=[('ee', 'Eesti'), ('ru', u'Русский'), ('en', 'English')])

    spacer = HiddenField('')
    username = StringField(lazy_gettext('Kasutajatunnus'), validators=[DataRequired(), Regexp('^[A-Za-z0-9]+$', message=lazy_gettext(u'Kasutajatunnus peab koosnema tähtedest ja numbritest')),
                                                         Length(max=10, message=lazy_gettext(u'Kasutajatunnus liiga pikk')), Length(min=2, message=lazy_gettext(u'Kasutajatunnus liiga lühike'))], description=lazy_gettext(u'Vali kasutajatunnus, mida plaanid kasutada süsteemi sisse logimiseks'))
    password = PasswordField(lazy_gettext('Parool'), validators=[DataRequired(), Length(min=4, message=lazy_gettext(u'Parool liiga lühike')), 
                                                   EqualTo('confirm', message=lazy_gettext(u'Parool ja parooli kordus ei ole identsed')),
                                                   Length(max=100)])
    confirm = PasswordField(lazy_gettext('Parooli kordus'))
    agree = BooleanField(lazy_gettext(u'Olen nõus, et minu andmeid kasutatakse informaatikavõistlustega seotud teavitusteks'), validators=[DataRequired(message=lazy_gettext(u'Puudub nõusolek andmete kasutamiseks'))])

    def validate_username(form, field):
        """Disallow usernames which are already present in the contest but associated with a different email"""
        if (db.session.query(User).join(Participation)
                .filter(Participation.contest_id == app.config['CONTEST_ID'])
                .filter(or_(User.email == None, User.email != form.email.data))
                .filter(User.username == field.data)).count():
            raise ValidationError(lazy_gettext("Antud kasutajatunnus on juba kasutusel"))


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
            flash(Markup(lazy_gettext(u'Kasutaja aktiveeritud. Peale võistluse algust saate sellele ligi lehel <a href="http://cms.eio.ee/">cms.eio.ee</a>.')), 'success')
            return redirect(url_for('blank'))
        else:
            flash(lazy_gettext(u'Vale või aegunud aktiveerimiskood'), 'danger')
    return render_template('activate.html', form=form)

# ---------------------------------------------------------------------------- #
class PasswordForm(Form):
    password = PasswordField(lazy_gettext('Uus parool'), validators=[DataRequired(), Length(min=4, message=lazy_gettext(u'Parool liiga lühike')), 
                                                   EqualTo('confirm', message=lazy_gettext(u'Parool ja parooli kordus ei ole identsed')),
                                                   Length(max=100)])
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
