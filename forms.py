from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired

class QueryForm(FlaskForm):
    artist_query = StringField('Artist', validators=[DataRequired()])
    submit = SubmitField('Search')

class EditForm(FlaskForm):
    new_tags = StringField('Tags', validators=[DataRequired()])
    submit = SubmitField('Update tags')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')