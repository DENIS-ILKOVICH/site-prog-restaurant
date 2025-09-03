from flask_wtf import *
from wtforms import *
from wtforms.validators import *
class LoginForm(FlaskForm):
    mail = StringField('Email: ', validators=[Email()])
    psw = PasswordField('Password: ', validators=[DataRequired(), Length(min=4, max=35)])
    remember = BooleanField('Remember me', default=False)
    submit = SubmitField('Sign in')