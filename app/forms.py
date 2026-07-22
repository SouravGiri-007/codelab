from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, BooleanField,
                     PasswordField, SubmitField, IntegerField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                ValidationError, Optional)
from flask_login import current_user
from app.models import User, NewsletterSubscription


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=64),
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6, max=128)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if not all(c.isalnum() or c in '_-' for c in field.data):
            raise ValidationError(
                'Username can only contain letters, numbers, underscores, and hyphens.'
            )
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError('This username is already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered.')


class SnippetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    body = TextAreaField('Code', validators=[DataRequired(), Length(max=50000)])
    language = SelectField('Language', validators=[DataRequired()], coerce=str)
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(max=300)])
    is_public = BooleanField('Public', default=True)
    submit = SubmitField('Save Snippet')


class CommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired(), Length(min=2, max=2000)])
    submit = SubmitField('Post Comment')


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    github_url = StringField('GitHub URL', validators=[Optional(), Length(max=200)])
    website_url = StringField('Website URL', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Update Profile')

    def validate_username(self, field):
        if field.data.lower() != current_user.username.lower():
            if User.query.filter_by(username=field.data.lower()).first():
                raise ValidationError('This username is already taken.')

    def validate_email(self, field):
        if field.data.lower() != current_user.email.lower():
            if User.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('This email is already registered.')


# ─── New: Newsletter Subscription ─────────────────────────────────────

class SubscribeForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Subscribe')

    def validate_email(self, field):
        existing = NewsletterSubscription.query.filter_by(email=field.data.lower()).first()
        if existing and existing.is_active:
            raise ValidationError('This email is already subscribed.')


# ─── New: Admin ───────────────────────────────────────────────────────

class AdminSettingForm(FlaskForm):
    news_fetch_interval = IntegerField('Fetch Interval (hours)',
                                       validators=[Optional()],
                                       default=4)
    news_max_per_fetch = IntegerField('Max Articles Per Source',
                                      validators=[Optional()],
                                      default=5)
    submit = SubmitField('Save Settings')