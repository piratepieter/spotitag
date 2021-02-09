from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class QueryForm(FlaskForm):
    artist_query = StringField('Artist', validators=[DataRequired()])
    submit = SubmitField('Search')

class EditForm(FlaskForm):
    new_tags = StringField('Tags', validators=[DataRequired()])
    submit = SubmitField('Update tags')
