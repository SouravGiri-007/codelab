import re
from functools import wraps
from flask import abort


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:30]


def parse_tags(tag_string):
    """Parse comma-separated tag string into list of cleaned tag names."""
    if not tag_string:
        return []
    tags = [t.strip().lower() for t in tag_string.split(',')]
    tags = [t for t in tags if t and len(t) <= 30]
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def truncate(text, length=100):
    """Truncate text to given length with ellipsis."""
    if not text or len(text) <= length:
        return text or ''
    return text[:length].rsplit(' ', 1)[0] + '...'


def language_label(lang_key, supported_languages):
    """Get display label for a language key."""
    for key, label in supported_languages:
        if key == lang_key:
            return label
    return lang_key.title()


def time_ago(dt):
    """Return a human-readable 'time ago' string."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Handle naive datetimes (SQLite) by assuming UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        return f'{seconds // 60}m ago'
    elif seconds < 86400:
        return f'{seconds // 3600}h ago'
    elif seconds < 2592000:
        return f'{seconds // 86400}d ago'
    elif seconds < 31536000:
        return f'{seconds // 2592000}mo ago'
    else:
        return f'{seconds // 31536000}y ago'


def init_app():
    """Initialize database tables and default admin settings.

    Call this inside an app context at startup (shared between run.py and
    wsgi.py so initialization logic stays in one place).
    """
    from app import db
    from app.models import AdminSetting

    db.create_all()

    defaults = {
        'ai_chat_enabled': 'true',
        'news_enabled': 'true',
        'email_enabled': 'true',
        'news_fetch_interval': '4',
    }
    for key, value in defaults.items():
        if not db.session.get(AdminSetting, key):
            db.session.add(AdminSetting(key=key, value=value))
    db.session.commit()