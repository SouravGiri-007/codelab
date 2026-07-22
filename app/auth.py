from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def register_user(username, email, password):
    """Create a new user account."""
    user = User(
        username=username.lower().strip(),
        email=email.lower().strip(),
        password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
        auth_provider='local'
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email, password):
    """Verify credentials and return User or None."""
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        return None
    # Google-only users don't have a password
    if not user.password_hash:
        return None
    if check_password_hash(user.password_hash, password):
        return user
    return None


def find_or_create_google_user(google_info):
    """
    Find an existing user by Google ID or email, or create a new one.

    Args:
        google_info: dict with keys 'sub', 'email', 'name', 'picture'

    Returns:
        User instance (existing or newly created)
    """
    google_id = google_info.get('sub')
    email = google_info.get('email', '').lower().strip()
    name = google_info.get('name', '')
    picture = google_info.get('picture', '')

    # 1. Look up by Google ID (returning user)
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        user.last_seen = datetime.now(timezone.utc)
        if picture:
            user.avatar_url = picture
        db.session.commit()
        return user

    # 2. Look up by email (link existing account)
    user = User.query.filter_by(email=email).first()
    if user:
        user.google_id = google_id
        user.auth_provider = 'both'
        user.last_seen = datetime.now(timezone.utc)
        if picture and not user.avatar_url:
            user.avatar_url = picture
        db.session.commit()
        return user

    # 3. Create a brand new user
    username = _generate_unique_username(email, name)

    user = User(
        username=username,
        email=email,
        password_hash=None,
        google_id=google_id,
        auth_provider='google',
        avatar_url=picture,
        bio='',
    )
    db.session.add(user)
    db.session.commit()
    return user


def _generate_unique_username(email, name):
    """
    Generate a unique username from the Google profile.
    Tries: name-based → email-based → email-based + number suffix.
    """
    # Try name first (e.g. "John Doe" → "johndoe")
    if name:
        base = ''.join(c for c in name.lower() if c.isalnum())
        if base and len(base) >= 3:
            if not User.query.filter_by(username=base).first():
                return base

    # Try email prefix (e.g. "john@gmail.com" → "john")
    base = email.split('@')[0].lower()
    base = ''.join(c for c in base if c.isalnum() or c in '_-')
    if len(base) < 3:
        base = 'user'

    if not User.query.filter_by(username=base).first():
        return base

    # Add numeric suffix until unique
    counter = 1
    while User.query.filter_by(username=f'{base}{counter}').first():
        counter += 1
    return f'{base}{counter}'