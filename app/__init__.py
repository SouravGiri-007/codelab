import logging
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from app.config import Config
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URI,
    strategy=Config.RATELIMIT_STRATEGY,
    enabled=Config.RATELIMIT_ENABLED,
)
oauth = OAuth()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)

    # Register Google OAuth provider
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_kwargs={'scope': 'openid email profile'},
    )

    # Import models so migrations can detect them
    from app.models import (User, Snippet, Tag, Comment, Like, SavedSnippet,
                            NewsArticle, NewsletterSubscription, ChatMessage, AdminSetting)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    from app.routes.news import news_bp
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    from app.routes.subscription import sub_bp
    from app.errors import errors

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sub_bp)
    app.register_blueprint(errors)

    # Pygments CSS for syntax highlighting (available in all templates)
    @app.context_processor
    def inject_pygments_css():
        from pygments.formatters import HtmlFormatter
        return {
            'get_pygments_css': lambda: HtmlFormatter().get_style_defs('.code-highlight')
        }

    # Global template context (available in ALL blueprints)
    from app.utils import language_label, time_ago
    from app.config import Config

    @app.context_processor
    def inject_globals():
        return {
            'supported_languages': Config.SUPPORTED_LANGUAGES,
            'language_label': language_label,
            'time_ago': time_ago,
        }

    # Custom template filters
    @app.template_filter('highlight')
    def highlight_code(code, language):
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, guess_lexer
        from pygments.formatters import HtmlFormatter

        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except Exception:
            try:
                lexer = guess_lexer(code)
            except Exception:
                lexer = get_lexer_by_name('text', stripall=True)

        formatter = HtmlFormatter(cssclass='code-highlight', linenos=True,
                                  lineanchors='line', anchorlinenos=True)
        return highlight(code, lexer, formatter)

    @app.template_filter('nl2br')
    def nl2br(text):
        if not text:
            return ''
        return text.replace('\n', '<br>')

    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        return time_ago(dt)

    # Shell context for Flask shell
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db, 'User': User, 'Snippet': Snippet, 'Tag': Tag,
            'Comment': Comment, 'Like': Like, 'SavedSnippet': SavedSnippet,
            'NewsArticle': NewsArticle, 'NewsletterSubscription': NewsletterSubscription,
            'ChatMessage': ChatMessage, 'AdminSetting': AdminSetting,
        }

    return app


def start_scheduler(app):
    """Start the APScheduler for background news fetching."""
    import asyncio
    from apscheduler.schedulers.background import BackgroundScheduler
    from app.services.news_service import run_news_fetch

    def fetch_job():
        logger.info("Scheduled news fetch starting...")
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            count = loop.run_until_complete(run_news_fetch())
            logger.info(f"Scheduled news fetch completed: {count} new articles")
        except Exception as e:
            logger.error(f"Scheduled news fetch failed: {e}")
        finally:
            if loop is not None:
                loop.close()

    scheduler = BackgroundScheduler()
    interval_hours = app.config.get('NEWS_FETCH_INTERVAL_HOURS', 4)
    scheduler.add_job(
        fetch_job,
        'interval',
        hours=interval_hours,
        id='news_fetch',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"News scheduler started (every {interval_hours} hours)")

    # Also do an initial fetch after 30 seconds
    import threading
    def initial_fetch():
        import time
        time.sleep(30)
        with app.app_context():
            fetch_job()

    thread = threading.Thread(target=initial_fetch, daemon=True)
    thread.start()