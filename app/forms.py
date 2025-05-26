from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL, Optional


class EmptyForm(FlaskForm):
    pass

class LikeForm(FlaskForm):
    submit = SubmitField('Like')

class RegisterForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PostForm(FlaskForm):
    content = TextAreaField('What’s happening?', validators=[DataRequired(), Length(max=280)])
    submit = SubmitField('Chirp')


class ProfileForm(FlaskForm):
    bio = StringField('Bio', validators=[Length(max=300), Optional()])
    location = StringField('Location', validators=[Length(max=100), Optional()])
    website = StringField('Website', validators=[URL(), Optional()])
    profile_pic = StringField('Profile Picture URL', validators=[URL(), Optional()])
    submit = SubmitField('Update Profile')