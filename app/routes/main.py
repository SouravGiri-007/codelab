from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, abort)
from flask_login import login_required, current_user
from app import db
from app.forms import SnippetForm, CommentForm
from app.models import User, Snippet, Tag, Comment, Like, SavedSnippet, tag_association
from app.utils import parse_tags, slugify, language_label, time_ago
from app.config import Config
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


# ─── Home & Explore ─────────────────────────────────────────────────
@main_bp.route('/')
@main_bp.route('/explore')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    lang = request.args.get('lang', '').strip()
    tag = request.args.get('tag', '').strip()
    sort = request.args.get('sort', 'newest')

    query = Snippet.query.filter_by(is_public=True, is_playground=False)

    # Search filter
    if search:
        query = query.filter(or_(
            Snippet.title.ilike(f'%{search}%'),
            Snippet.description.ilike(f'%{search}%'),
            Snippet.body.ilike(f'%{search}%'),
            Snippet.tags.any(Tag.name.ilike(f'%{search}%'))
        ))

    # Language filter
    if lang:
        query = query.filter_by(language=lang)

    # Tag filter
    if tag:
        query = query.filter(Snippet.tags.any(Tag.slug == tag.lower()))

    # Sorting
    if sort == 'oldest':
        query = query.order_by(Snippet.created_at.asc())
    elif sort == 'popular':
        query = query.outerjoin(Like).group_by(Snippet.id).order_by(
            db.func.count(Like.id).desc(), Snippet.created_at.desc()
        )
    elif sort == 'comments':
        query = query.outerjoin(Comment).group_by(Snippet.id).order_by(
            db.func.count(Comment.id).desc(), Snippet.created_at.desc()
        )
    else:  # newest
        query = query.order_by(Snippet.created_at.desc())

    snippets = query.paginate(
        page=page,
        per_page=current_app.config['SNIPPETS_PER_PAGE'],
        error_out=False
    )

    # Get popular tags for sidebar
    popular_tags = Tag.query.join(
        tag_association, Tag.id == tag_association.c.tag_id
    ).join(Snippet).filter(
        Snippet.is_public == True
    ).group_by(Tag.id).order_by(
        db.func.count(Snippet.id).desc()
    ).limit(20).all()

    # Get language counts for filter
    lang_counts = db.session.query(
        Snippet.language, db.func.count(Snippet.id)
    ).filter(
        Snippet.is_public == True, Snippet.is_playground == False
    ).group_by(Snippet.language).order_by(
        db.func.count(Snippet.id).desc()
    ).all()

    return render_template('snippets/explore.html',
                           snippets=snippets,
                           popular_tags=popular_tags,
                           lang_counts=lang_counts,
                           search=search, lang=lang, tag=tag, sort=sort)


# ─── Snippet Detail ─────────────────────────────────────────────────
@main_bp.route('/snippet/<int:id>', methods=['GET'])
def view_snippet(id):
    snippet = Snippet.query.get_or_404(id)

    # Check access
    if not snippet.is_public and snippet.user_id != (current_user.id if current_user.is_authenticated else 0):
        abort(403)

    comment_form = CommentForm() if current_user.is_authenticated else None

    # Pre-compute like/save status for template (Jinja2 can't call methods with args)
    is_liked = False
    is_saved = False
    if current_user.is_authenticated:
        is_liked = Like.query.filter_by(user_id=current_user.id, snippet_id=id).first() is not None
        is_saved = SavedSnippet.query.filter_by(user_id=current_user.id, snippet_id=id).first() is not None

    return render_template('snippets/detail.html',
                           snippet=snippet,
                           comment_form=comment_form,
                           is_liked=is_liked,
                           is_saved=is_saved)


# ─── Create Snippet ─────────────────────────────────────────────────
@main_bp.route('/snippet/new', methods=['GET', 'POST'])
@login_required
def new_snippet():
    form = SnippetForm()
    form.language.choices = current_app.config['SUPPORTED_LANGUAGES']

    if form.validate_on_submit():
        snippet = Snippet(
            title=form.title.data.strip(),
            body=form.body.data,
            language=form.language.data,
            description=(form.description.data or '').strip(),
            is_public=form.is_public.data,
            user_id=current_user.id
        )

        # Handle tags
        tag_names = parse_tags(form.tags.data)
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                db.session.add(tag)
            snippet.tags.append(tag)

        db.session.add(snippet)
        db.session.commit()

        flash('Snippet created!', 'success')
        return redirect(url_for('main.view_snippet', id=snippet.id))

    return render_template('snippets/form.html', form=form, mode='create')


# ─── Edit Snippet ───────────────────────────────────────────────────
@main_bp.route('/snippet/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_snippet(id):
    snippet = Snippet.query.get_or_404(id)
    if snippet.user_id != current_user.id:
        abort(403)

    form = SnippetForm(obj=snippet)
    form.language.choices = current_app.config['SUPPORTED_LANGUAGES']

    if form.validate_on_submit():
        snippet.title = form.title.data.strip()
        snippet.body = form.body.data
        snippet.language = form.language.data
        snippet.description = (form.description.data or '').strip()
        snippet.is_public = form.is_public.data

        # Update tags
        tag_names = parse_tags(form.tags.data)
        snippet.tags.clear()
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                db.session.add(tag)
            snippet.tags.append(tag)

        db.session.commit()
        flash('Snippet updated!', 'success')
        return redirect(url_for('main.view_snippet', id=snippet.id))

    # Pre-fill tags
    form.tags.data = ', '.join([t.name for t in snippet.tags])
    return render_template('snippets/form.html', form=form, mode='edit',
                           snippet=snippet)


# ─── Delete Snippet ─────────────────────────────────────────────────
@main_bp.route('/snippet/<int:id>/delete', methods=['POST'])
@login_required
def delete_snippet(id):
    snippet = Snippet.query.get_or_404(id)
    if snippet.user_id != current_user.id:
        abort(403)

    db.session.delete(snippet)
    db.session.commit()
    flash('Snippet deleted.', 'info')
    return redirect(url_for('main.index'))


# ─── Like / Unlike ──────────────────────────────────────────────────
@main_bp.route('/snippet/<int:id>/like', methods=['POST'])
@login_required
def toggle_like(id):
    snippet = Snippet.query.get_or_404(id)
    if not snippet.is_public:
        abort(403)

    existing = Like.query.filter_by(user_id=current_user.id, snippet_id=id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    else:
        like = Like(user_id=current_user.id, snippet_id=id)
        db.session.add(like)
        db.session.commit()

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return {'liked': existing is None, 'count': snippet.like_count}
    return redirect(url_for('main.view_snippet', id=id))


# ─── Save / Unsave ──────────────────────────────────────────────────
@main_bp.route('/snippet/<int:id>/save', methods=['POST'])
@login_required
def toggle_save(id):
    snippet = Snippet.query.get_or_404(id)

    existing = SavedSnippet.query.filter_by(user_id=current_user.id, snippet_id=id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Removed from saved.', 'info')
    else:
        saved = SavedSnippet(user_id=current_user.id, snippet_id=id)
        db.session.add(saved)
        db.session.commit()
        flash('Snippet saved!', 'success')

    return redirect(url_for('main.view_snippet', id=id))


# ─── Comments ───────────────────────────────────────────────────────
@main_bp.route('/snippet/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    snippet = Snippet.query.get_or_404(id)
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            body=form.body.data.strip(),
            user_id=current_user.id,
            snippet_id=id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted!', 'success')

    return redirect(url_for('main.view_snippet', id=id))


@main_bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    if comment.user_id != current_user.id:
        abort(403)

    snippet_id = comment.snippet_id
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('main.view_snippet', id=snippet_id))


# ─── Saved Snippets ─────────────────────────────────────────────────
@main_bp.route('/saved')
@login_required
def saved_snippets():
    page = request.args.get('page', 1, type=int)
    saved = SavedSnippet.query.filter_by(user_id=current_user.id).order_by(
        SavedSnippet.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config['SNIPPETS_PER_PAGE'],
        error_out=False
    )
    return render_template('snippets/saved.html', snippets=saved)


# ─── My Snippets ────────────────────────────────────────────────────
@main_bp.route('/my-snippets')
@login_required
def my_snippets():
    page = request.args.get('page', 1, type=int)
    snippets = Snippet.query.filter_by(user_id=current_user.id).order_by(
        Snippet.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config['SNIPPETS_PER_PAGE'],
        error_out=False
    )
    return render_template('snippets/my_snippets.html', snippets=snippets)


# ─── Playground ─────────────────────────────────────────────────────
@main_bp.route('/playground')
def playground():
    """Code playground page — write & preview code with syntax highlighting."""
    form = SnippetForm()
    form.language.choices = current_app.config['SUPPORTED_LANGUAGES']
    return render_template('snippets/playground.html', form=form)


# ─── Tags Page ──────────────────────────────────────────────────────
@main_bp.route('/tags')
def tags():
    all_tags = Tag.query.join(
        tag_association, Tag.id == tag_association.c.tag_id
    ).join(Snippet).filter(
        Snippet.is_public == True
    ).group_by(Tag.id).order_by(
        db.func.count(Snippet.id).desc()
    ).all()

    return render_template('snippets/tags.html', tags=all_tags)


# ─── Vercel Cron Job Endpoint ──────────────────────────────────────────
@main_bp.route('/api/cron/news-fetch')
def cron_news_fetch():
    """
    Vercel Cron Job handler for news fetching.

    Triggered by the cron schedule defined in vercel.json.
    In production with a real database and API keys, this route would
    call run_news_fetch() to aggregate and store new articles.

    Requires Vercel Pro (Cron Jobs are not available on the free tier).
    """
    return {'success': True, 'data': {'note': 'News fetch cron endpoint (not yet implemented)'}}