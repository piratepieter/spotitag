import os

class Config(object):
    SECRET_KEY = os.environ['SPOTITAG_SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
