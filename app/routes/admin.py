"""Admin routes — dashboard and management."""
import asyncio
import logging
from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, current_app, abort)
from flask_login import login_required, current_user
from app import db
from app.models import (User, Snippet, NewsArticle, NewsletterSubscription,
                        ChatMessage, AdminSetting, Tag, Comment, Like)
from app.forms import AdminSettingForm

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator: require admin access."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def get_setting(key, default=''):
    """Get an admin setting value."""
    s = AdminSetting.query.get(key)
    return s.value if s else default


def set_setting(key, value):
    """Set an admin setting value."""
    s = AdminSetting.query.get(key)
    if s:
        s.value = str(value)
    else:
        s = AdminSetting(key=key, value=str(value))
        db.session.add(s)


# ─── Dashboard ────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with stats."""
    stats = {
        'total_users': User.query.count(),
        'total_snippets': Snippet.query.count(),
        'total_news': NewsArticle.query.count(),
        'published_news': NewsArticle.query.filter_by(is_published=True).count(),
        'total_subscribers': NewsletterSubscription.query.filter_by(is_active=True).count(),
        'total_chat_messages': ChatMessage.query.count(),
        'total_comments': Comment.query.count(),
        'total_likes': Like.query.count(),
        'total_tags': Tag.query.count(),
    }

    # Recent news
    recent_news = NewsArticle.query.order_by(
        NewsArticle.created_at.desc()
    ).limit(5).all()

    # Recent users
    recent_users = User.query.order_by(
        User.created_at.desc()
    ).limit(5).all()

    # Feature toggles
    features = {
        'ai_chat_enabled': get_setting('ai_chat_enabled', 'true').lower() == 'true',
        'news_enabled': get_setting('news_enabled', 'true').lower() == 'true',
        'email_enabled': get_setting('email_enabled', 'true').lower() == 'true',
        'news_fetch_interval': get_setting('news_fetch_interval', '4'),
    }

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_news=recent_news,
                           recent_users=recent_users,
                           features=features)


# ─── News Management ──────────────────────────────────────────────────

@admin_bp.route('/news')
@admin_required
def news_management():
    """Manage news articles."""
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '').strip()

    query = NewsArticle.query
    if source:
        query = query.filter(NewsArticle.source == source)
    query = query.order_by(NewsArticle.created_at.desc())

    articles = query.paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    return render_template('admin/news.html', articles=articles, source=source)


@admin_bp.route('/news/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_news(id):
    """Publish/unpublish a news article."""
    article = NewsArticle.query.get_or_404(id)
    article.is_published = not article.is_published
    db.session.commit()
    status = 'published' if article.is_published else 'unpublished'
    flash(f'Article {status}.', 'success')
    return redirect(url_for('admin.news_management'))


@admin_bp.route('/news/<int:id>/delete', methods=['POST'])
@admin_required
def delete_news(id):
    """Delete a news article."""
    article = NewsArticle.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'info')
    return redirect(url_for('admin.news_management'))


@admin_bp.route('/news/fetch', methods=['POST'])
@admin_required
def manual_fetch():
    """Manually trigger news fetch."""
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from app.services.news_service import run_news_fetch
        count = loop.run_until_complete(run_news_fetch())
        flash(f'Fetched {count} new articles!', 'success')
    except Exception as e:
        logger.error(f"Manual fetch failed: {e}")
        flash(f'Fetch failed: {str(e)}', 'danger')
    finally:
        if loop is not None:
            loop.close()
    return redirect(url_for('admin.news_management'))


# ─── Subscription Management ──────────────────────────────────────────

@admin_bp.route('/subscriptions')
@admin_required
def subscriptions():
    """Manage newsletter subscriptions."""
    page = request.args.get('page', 1, type=int)
    show_inactive = request.args.get('all', '').strip() == '1'

    query = NewsletterSubscription.query
    if not show_inactive:
        query = query.filter_by(is_active=True)
    query = query.order_by(NewsletterSubscription.subscribed_at.desc())

    subs = query.paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    return render_template('admin/subscriptions.html',
                           subscriptions=subs,
                           show_inactive=show_inactive)


@admin_bp.route('/subscriptions/<int:id>/delete', methods=['POST'])
@admin_required
def delete_subscription(id):
    """Delete a subscription."""
    sub = NewsletterSubscription.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash('Subscription deleted.', 'info')
    return redirect(url_for('admin.subscriptions'))


# ─── Settings ─────────────────────────────────────────────────────────

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Admin settings — feature toggles and configuration."""
    form = AdminSettingForm()

    if request.method == 'POST':
        # Feature toggles
        ai_chat = 'ai_chat_enabled' in request.form
        news_enabled = 'news_enabled' in request.form
        email_enabled = 'email_enabled' in request.form
        fetch_interval = request.form.get('news_fetch_interval', '4')

        set_setting('ai_chat_enabled', str(ai_chat).lower())
        set_setting('news_enabled', str(news_enabled).lower())
        set_setting('email_enabled', str(email_enabled).lower())
        set_setting('news_fetch_interval', fetch_interval)

        db.session.commit()
        flash('Settings saved!', 'success')
        return redirect(url_for('admin.settings'))

    # Load current settings
    return render_template('admin/settings.html',
                           ai_chat=get_setting('ai_chat_enabled', 'true').lower() == 'true',
                           news_enabled=get_setting('news_enabled', 'true').lower() == 'true',
                           email_enabled=get_setting('email_enabled', 'true').lower() == 'true',
                           fetch_interval=get_setting('news_fetch_interval', '4'),
                           form=form)


# ─── Users Management ─────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def users():
    """View all users."""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(id):
    """Toggle admin status for a user."""
    if id == current_user.id:
        flash("You can't change your own admin status.", 'danger')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(id)
    user.is_admin = not user.is_admin
    db.session.commit()
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin access {status} for {user.username}.', 'success')
    return redirect(url_for('admin.users'))