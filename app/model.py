from flask_login import UserMixin

from .app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    profile_image = db.Column(db.String(255), nullable=False, default='')
    password = db.Column(db.String(200), nullable=False)
