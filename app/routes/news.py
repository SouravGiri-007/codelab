"""News routes — public news pages."""
from flask import Blueprint, render_template, redirect, url_for, request, current_app, abort
from app import db
from app.models import NewsArticle
from sqlalchemy import or_

news_bp = Blueprint('news', __name__)


@news_bp.route('/news')
def news_list():
    """Browse all published news articles."""
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '').strip()
    search = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'newest')

    query = NewsArticle.query.filter_by(is_published=True)

    if source:
        query = query.filter(NewsArticle.source == source)

    if search:
        query = query.filter(or_(
            NewsArticle.title.ilike(f'%{search}%'),
            NewsArticle.summary.ilike(f'%{search}%'),
        ))

    if sort == 'popular':
        query = query.order_by(NewsArticle.upvotes.desc(), NewsArticle.created_at.desc())
    else:
        query = query.order_by(NewsArticle.created_at.desc())

    articles = query.paginate(
        page=page,
        per_page=current_app.config.get('NEWS_PER_PAGE', 10),
        error_out=False
    )

    # Source counts for filter sidebar
    source_counts = dict(
        db.session.query(NewsArticle.source, db.func.count(NewsArticle.id))
        .filter(NewsArticle.is_published == True)
        .group_by(NewsArticle.source).all()
    )
    total_articles = sum(source_counts.values())

    return render_template('news/list.html',
                           articles=articles,
                           source=source,
                           search=search,
                           sort=sort,
                           source_counts=source_counts,
                           total_articles=total_articles)


@news_bp.route('/news/<int:id>')
def news_detail(id):
    """View a single news article (redirects to external source)."""
    article = NewsArticle.query.get_or_404(id)
    if not article.is_published:
        abort(404)
    return render_template('news/detail.html', article=article)