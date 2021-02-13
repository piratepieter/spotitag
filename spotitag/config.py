import os

class Config(object):
    SECRET_KEY = 'omg'
    SQLALCHEMY_DATABASE_URI = os.environ['SPOTITAG_URI']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
