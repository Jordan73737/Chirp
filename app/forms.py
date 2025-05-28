from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL, Optional
from flask_wtf.file import FileField, FileAllowed


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
    content = TextAreaField('Chirp:', validators=[DataRequired(), Length(max=280)])
    submit = SubmitField('Chirp')

class ProfileForm(FlaskForm):
    bio = TextAreaField('Bio')
    location = StringField('Location')
    website = StringField('Website')
    profile_pic = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save')

