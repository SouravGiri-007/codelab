import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY environment variable is required. "
            "Set it to a random string of at least 32 characters."
        )
    SQLALCHEMY_DATABASE_URI = os.environ.get('CODELAB_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'codelab.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session & Security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get('ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Pagination
    SNIPPETS_PER_PAGE = 12
    NEWS_PER_PAGE = 10
    MAX_SNIPPET_TITLE_LENGTH = 120
    MAX_SNIPPET_BODY_LENGTH = 50000
    MAX_TAG_LENGTH = 30

    # Supported languages for the playground
    SUPPORTED_LANGUAGES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('ruby', 'Ruby'),
        ('php', 'PHP'),
        ('sql', 'SQL'),
        ('bash', 'Bash/Shell'),
        ('typescript', 'TypeScript'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('r', 'R'),
        ('scala', 'Scala'),
        ('lua', 'Lua'),
        ('perl', 'Perl'),
    ]

    # ─── AI (Groq) ──────────────────────────────────────────────────
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_BASE_URL = 'https://api.groq.com/openai/v1'
    DEFAULT_CHAT_MODEL = os.environ.get('DEFAULT_CHAT_MODEL') or \
        'llama-3.1-8b-instant'
    NEWS_MODEL = os.environ.get('NEWS_MODEL') or \
        'llama-3.1-8b-instant'

    # Available models for user selection in chat (Groq-hosted)
    CHAT_MODELS = [
        ('llama-3.1-8b-instant', 'Llama 3.1 8B Instant'),
        ('llama-3.3-70b-versatile', 'Llama 3.3 70B Versatile'),
        ('gemma2-9b-it', 'Gemma 2 9B'),
        ('mixtral-8x7b-32768', 'Mixtral 8x7B'),
        ('llama-3.1-70b-versatile', 'Llama 3.1 70B Versatile'),
    ]
    
    # ─── Email (Resend — placeholder) ─────────────────────────────
    # RESEND_API_KEY is available for future use if needed.

    # ─── News Aggregation ──────────────────────────────────────────
    NEWS_FETCH_INTERVAL_HOURS = 4
    NEWS_MAX_PER_FETCH = 5  # per source
    NEWS_SOURCES = ['hackernews', 'devto', 'reddit']
# --- Email Infrastructure Configuration ---
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    MAIL_FROM = os.environ.get("MAIL_FROM", "")
    MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "CodeLab")

    # ─── Rate Limiting ────────────────────────────────────────────
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'true').lower() == 'true'
    RATELIMIT_DEFAULT = '200/hour;20/minute'
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True

    # ─── Google OAuth ─────────────────────────────────────────────
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'