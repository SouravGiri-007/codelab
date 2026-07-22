"""
Production entry point for Gunicorn / Render.

This module is used by the production WSGI server (Gunicorn) instead of
run.py. It does everything run.py does, but at module-import time so
Gunicorn workers pick up the initialized app with scheduler running.

Usage:
    gunicorn wsgi:app -w 4 -b 0.0.0.0:8000

Or on Render (Procfile):
    web: gunicorn wsgi:app --worker-class sync --timeout 120 --access-logfile -
"""

import os
import sys

# Ensure we're running from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, start_scheduler
from app.utils import init_app

# Create the Flask application
app = create_app()

# --- Database initialization & scheduler startup ---
# These run once when Gunicorn loads the module (worker startup).
print(" * Initializing CodeLab database...")
with app.app_context():
    init_app()
print(" * Database ready.")

# Start the news scheduler (skipped when VERCEL=1 or DISABLE_SCHEDULER=1)
if os.environ.get('VERCEL', '') != '1' and os.environ.get('DISABLE_SCHEDULER', '') != '1':
    print(" * Starting news scheduler...")
    start_scheduler(app)
else:
    print(" * News scheduler disabled (VERCEL or DISABLE_SCHEDULER set)")
