from datetime import datetime, timezone
from urllib.parse import urlparse
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, session)
from flask_login import login_required, login_user, logout_user, current_user
from app.forms import LoginForm, RegistrationForm, ProfileForm
from app.auth import register_user, authenticate_user, find_or_create_google_user
from app.models import User, Snippet, db
from app.utils import time_ago
from app import oauth, limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5/hour;2/10minutes', override_defaults=False)
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10/hour;5/15minutes', override_defaults=False)
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(
            email=form.email.data,
            password=form.password.data
        )
        if user:
            login_user(user, remember=form.remember_me.data)
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()
            flash('Welcome back!', 'success')

            next_page = request.args.get('next')
            if next_page:
                # Validate redirect target — only allow relative URLs
                parsed = urlparse(next_page)
                if not parsed.netloc and not parsed.scheme:
                    return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            # Check if this is a Google-only user trying email/password login
            existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
            if existing and not existing.password_hash:
                flash('This account uses Google Sign-In. Please click "Sign in with Google" below.', 'warning')
            else:
                flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    query = Snippet.query.filter_by(user_id=user.id)
    if not current_user.is_authenticated or current_user.id != user.id:
        query = query.filter_by(is_public=True)

    snippets = query.order_by(Snippet.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config['SNIPPETS_PER_PAGE'],
        error_out=False
    )

    return render_template('auth/profile.html', user=user, snippets=snippets,
                           time_ago=time_ago)


@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data.lower().strip()
        current_user.email = form.email.data.lower().strip()
        current_user.bio = form.bio.data
        current_user.github_url = form.github_url.data.strip()
        current_user.website_url = form.website_url.data.strip()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile', username=current_user.username))

    return render_template('auth/settings.html', form=form)


# ─── Google OAuth ─────────────────────────────────────────────────────

@auth_bp.route('/google/login')
@limiter.limit('10/hour;5/15minutes', override_defaults=False)
def google_login():
    """Initiate Google OAuth 2.0 login flow."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Generate nonce for OpenID Connect
    import secrets
    nonce = secrets.token_urlsafe(32)
    session['google_auth_nonce'] = nonce

    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)


@auth_bp.route('/google/callback')
@limiter.limit('20/hour;10/30minutes', override_defaults=False)
def google_callback():
    """Handle the OAuth callback from Google."""
    try:
        token = oauth.google.authorize_access_token()

        # Verify and parse the ID token
        nonce = session.pop('google_auth_nonce', None)
        user_info = oauth.google.parse_id_token(token, nonce=nonce)

        if not user_info or not user_info.get('email'):
            flash('Could not retrieve your Google account information.', 'danger')
            return redirect(url_for('auth.login'))

        # Find or create the user
        user = find_or_create_google_user(user_info)
        login_user(user, remember=True)
        user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

        flash(f'Welcome, {user.username}!', 'success')

        next_page = request.args.get('next')
        if next_page:
            # Validate redirect target — only allow relative URLs
            parsed = urlparse(next_page)
            if not parsed.netloc and not parsed.scheme:
                return redirect(next_page)
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('Google sign-in failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))