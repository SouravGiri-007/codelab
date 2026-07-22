import os
import sys
import logging

# Ensure we're running from the project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Provide a dev secret key if not set via environment (never used in production)
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

from app import create_app, db, start_scheduler
from app.models import (User, Snippet, Tag, Comment, Like, SavedSnippet,
                        NewsArticle, NewsletterSubscription, ChatMessage, AdminSetting)
from app.utils import init_app

app = create_app()

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print(" * Initializing CodeLab database...")
    with app.app_context():
        init_app()
    print(" * Database ready.")

    # Start the news scheduler (skipped when VERCEL=1 or DISABLE_SCHEDULER=1)
    if os.environ.get('VERCEL', '') != '1' and os.environ.get('DISABLE_SCHEDULER', '') != '1':
        print(" * Starting news scheduler...")
        start_scheduler(app)
    else:
        print(" * News scheduler disabled (Vercel or DISABLE_SCHEDULER=1)")

    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    print(f" * CodeLab running at http://127.0.0.1:5000 (debug={'on' if debug_mode else 'off'})")
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)