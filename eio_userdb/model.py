# -*- coding: UTF-8 -*-
"""
EIO user registration webapp :: SQLAlchemy models.

Copyright 2014-2021, EIO Team.
License: MIT
"""
from datetime import timedelta

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import ColumnClause
from sqlalchemy.dialects.postgresql import ARRAY, CIDR
from .cmscommon.crypto import *

db = SQLAlchemy()
Base = db.Model

def _saobject_repr(self):
    s = [self.__class__.__name__, '\n']
    for c in self.__class__.__table__.columns:
        s.extend([u'\t', c.name, u': ', unicode(getattr(self, c.name)), u'\n'])
    return ''.join(s).encode('utf8')
Base.__repr__ = _saobject_repr


class UserInfo(Base):
    __tablename__ = 'user_info'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    category = Column(String, nullable=False)
    school = Column(Unicode, nullable=False)
    grade = Column(Unicode, nullable=False)
    code_lang = Column(Unicode, nullable=True)
    text_lang = Column(Unicode, nullable=True)
    registration_time = Column(DateTime)
    registration_ip = Column(String)
    activated = Column(Boolean, default=False)

    def activation_code(self, salt):
        import hashlib
        from .main import app
        m = hashlib.md5()
        m.update(app.config['SECRET_KEY'].encode('utf-8'))
        m.update(self.user.email.encode('utf-8'))
        m.update(b'|')
        m.update(self.user.password.encode('utf-8'))
        m.update(b'|')
        m.update(str(salt).encode('utf8'))
        return '$%d$%s' % (self.id, m.hexdigest())

# ------------ Copy pasted from CMS codebase (with some changes) ----------- #

class CodenameConstraint(CheckConstraint):
    """Check that the column uses a limited alphabet."""

    def __init__(self, column_name):
        column = ColumnClause(column_name)
        super(CodenameConstraint, self).__init__(
            column.op("~")(literal_column("'^[A-Za-z0-9_-]+$'")))


# The 'user' table used by CMS
class User(Base):
    __tablename__ = 'users'

    # Auto increment primary key.
    id = Column(
        Integer,
        primary_key=True)

    # Real name (human readable) of the user.
    first_name = Column(
        Unicode,
        nullable=False)
    last_name = Column(
        Unicode,
        nullable=False)

    # Username and password to log in the CWS.
    username = Column(
        Unicode,
        #CodenameConstraint("username"), # SQLite does not support this
        nullable=False,
        unique=True)
    password = Column(
        Unicode,
        nullable=False,
        default=lambda: build_password(generate_random_password()))

    # Email for any communications in case of remote contest.
    email = Column(
        Unicode,
        nullable=True)

    # Timezone for the user. All timestamps in CWS will be shown using
    # the timezone associated to the logged-in user or (if it's None
    # or an invalid string) the timezone associated to the contest or
    # (if it's None or an invalid string) the local timezone of the
    # server. This value has to be a string like "Europe/Rome",
    # "Australia/Sydney", "America/New_York", etc.
    timezone = Column(
        Unicode,
        nullable=True)

    # The language codes accepted by this user (from the "most
    # preferred" to the "least preferred"). If in a contest there is a
    # statement available in some of these languages, then the most
    # preferred of them will be highlighted.
    # FIXME: possibly move it to Participation and change it back to
    # primary_statements
    preferred_languages = Column(
        ARRAY(String),
        nullable=False,
        default=[])

    # These one-to-many relationships are the reversed directions of
    # the ones defined in the "child" classes using foreign keys.

    participations = relationship(
        "Participation",
        cascade = "all, delete-orphan",
        passive_deletes = True,
        back_populates="user")

    user_info = relationship(
        "UserInfo",
        cascade="all, delete-orphan",
        uselist=False,
        backref="user")

class Participation(Base):
    """Class to store a single participation of a user in a contest.

    """
    __tablename__ = 'participations'

    # Auto increment primary key.
    id = Column(
        Integer,
        primary_key=True)

    # Starting time: for contests where every user has at most x hours
    # of the y > x hours totally available, this is the time the user
    # decided to start their time-frame.
    starting_time = Column(
        DateTime,
        nullable=True)

    # A shift in the time interval during which the user is allowed to
    # submit.
    delay_time = Column(
        Interval,
        nullable=False,
        default=timedelta())

    # An extra amount of time allocated for this user.
    extra_time = Column(
        Interval,
        nullable=False,
        default=timedelta())

    # Contest-specific password. If this password is not null then the
    # traditional user.password field will be "replaced" by this field's
    # value (only for this participation).
    password = Column(
        Unicode,
        nullable=True)

    # A hidden participation (e.g. does not appear in public rankings), can
    # also be used for debugging purposes.
    hidden = Column(
        Boolean,
        nullable=False,
        default=False)

    # An unrestricted participation (e.g. contest time,
    # maximum number of submissions, minimum interval between submissions,
    # maximum number of user tests, minimum interval between user tests),
    # can also be used for debugging purposes.
    unrestricted = Column(
        Boolean,
        nullable=False,
        default=False)

    # Contest (id and object) to which the user is participating.
    contest_id = Column(
        Integer,
        nullable=False,
        index=True)

    # User (id and object) which is participating.
    user_id = Column(
        Integer,
        ForeignKey(User.id,
                   onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True)
    user = relationship(
        User,
        back_populates="participations")
    __table_args__ = (UniqueConstraint('contest_id', 'user_id'),)

    # Team (id and object) that the user is representing with this
    # participation.
    team_id = Column(Integer, nullable=True)

    # The divison the user participates in.
    division = Column(
        String,
        nullable=True)


# Sample database setup
def init_db():
    from .main import app
    with app.app_context():
        db.create_all()

def init_sample_data():
    from .main import app
    with app.app_context():
        u = User(id=1, username='testuser', first_name=u'Jüriöö', last_name=u'Ülestõus', email='kt@ut.ee', password='plaintext:parool')
        ui = UserInfo(id=1, category='other', school=u'Jääääre gümnaasium', grade='IV')
        p = Participation(id=1, user_id=1, contest_id=app.config['CONTEST_ID'])
        db.session.add(u)
        db.session.add(ui)
        db.session.add(p)
        db.session.commit()
