# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: DB admin

Copyright 2014, EIO Team.
License: MIT
"""
from flask import flash, redirect, url_for, render_template, request
import flask_admin as admin
import flask_login as login
from flask_admin import expose
from flask_admin.contrib import sqla

from flask_wtf import Form
from wtforms.fields import PasswordField
from wtforms.validators import DataRequired, AnyOf

from .model import User
from .main import app, db

class DumbUser(login.UserMixin):
    def __init__(self, id):
        self.id = id

login_manager = login.LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return DumbUser(userid)

class LoginForm(Form):
    password = PasswordField(validators=[DataRequired(), AnyOf([app.config['SECRET_PASSWORD']], message="Wrong password")])

class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        form = LoginForm()
        if form.validate_on_submit():
            login.login_user(DumbUser(1))
            flash("Logged in successfully.", "success")
            return redirect(request.args.get("next") or url_for(".index"))
        return render_template("login.html", form=form)
    
    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        flash("Logged out successfully", "success")
        return redirect(url_for('index'))

class MyModelView(sqla.ModelView):
    page_size = 500
    def is_accessible(self):
        return not login.current_user.is_anonymous()

admin = admin.Admin(app, index_view=MyAdminIndexView())
#admin.add_view(MyModelView(Registration, db.session))
admin.add_view(MyModelView(User, db.session))
