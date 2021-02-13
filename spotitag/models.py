from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from spotitag import db, login


from collections import defaultdict
TAG_TABLE = defaultdict(lambda: defaultdict(list))


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tags = db.relationship('Tag', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.username


class Tag(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return self.label


class Artist(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(32), index=True, unique=True)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))