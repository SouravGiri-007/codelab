from flask import (Blueprint, request, jsonify, current_app, abort)
from flask_login import login_required, current_user
from app import db
from app.models import User, Snippet, Tag, Comment, Like, SavedSnippet, tag_association
from app.utils import parse_tags, slugify, time_ago
from sqlalchemy import or_

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# ─── Envelope Helpers ───────────────────────────────────────────────

def api_success(data, status=200):
    """Return a consistent success response."""
    return jsonify({'success': True, 'data': data}), status


def api_error(message, status=400):
    """Return a consistent error response."""
    return jsonify({'success': False, 'error': message}), status


def snippet_to_dict(snippet):
    """Convert a snippet model to JSON-serializable dict."""
    return {
        'id': snippet.id,
        'title': snippet.title,
        'body': snippet.body,
        'language': snippet.language,
        'description': snippet.description,
        'is_public': snippet.is_public,
        'tags': [t.name for t in snippet.tags],
        'author': {
            'username': snippet.author.username,
            'id': snippet.author.id,
        },
        'likes': snippet.like_count,
        'comments': snippet.comment_count,
        'created_at': snippet.created_at.isoformat(),
        'updated_at': snippet.updated_at.isoformat(),
    }


# ─── List Snippets ──────────────────────────────────────────────────
@api_bp.route('/snippets', methods=['GET'])
def list_snippets():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '').strip()
    lang = request.args.get('lang', '').strip()
    tag = request.args.get('tag', '').strip()
    sort = request.args.get('sort', 'newest')
    author = request.args.get('author', '').strip()

    query = Snippet.query.filter_by(is_public=True)

    if search:
        query = query.filter(or_(
            Snippet.title.ilike(f'%{search}%'),
            Snippet.description.ilike(f'%{search}%'),
            Snippet.body.ilike(f'%{search}%'),
            Snippet.tags.any(Tag.name.ilike(f'%{search}%'))
        ))

    if lang:
        query = query.filter_by(language=lang)

    if tag:
        query = query.filter(Snippet.tags.any(Tag.slug == tag.lower()))

    if author:
        user = User.query.filter_by(username=author).first()
        if user:
            query = query.filter_by(user_id=user.id)

    if sort == 'popular':
        query = query.outerjoin(Like).group_by(Snippet.id).order_by(
            db.func.count(Like.id).desc()
        )
    elif sort == 'oldest':
        query = query.order_by(Snippet.created_at.asc())
    else:
        query = query.order_by(Snippet.created_at.desc())

    per_page = min(per_page, 50)  # Cap at 50
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return api_success({
        'snippets': [snippet_to_dict(s) for s in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
    })


# ─── Get Single Snippet ─────────────────────────────────────────────
@api_bp.route('/snippets/<int:id>', methods=['GET'])
def get_snippet(id):
    snippet = Snippet.query.get_or_404(id)
    if not snippet.is_public and snippet.user_id != (current_user.id if current_user.is_authenticated else 0):
        abort(403)
    return api_success(snippet_to_dict(snippet))


# ─── Create Snippet (API) ───────────────────────────────────────────
@api_bp.route('/snippets', methods=['POST'])
@login_required
def create_snippet():
    data = request.get_json()
    if not data:
        return api_error('JSON body required')

    title = data.get('title', '').strip()
    body = data.get('body', '')
    language = data.get('language', 'python')
    description = data.get('description', '').strip()
    is_public = data.get('is_public', True)
    tags_raw = data.get('tags', '')

    if not title or not body:
        return api_error('Title and body are required.')

    if len(title) > current_app.config['MAX_SNIPPET_TITLE_LENGTH']:
        return api_error('Title too long.')

    # Validate language
    valid_langs = [l[0] for l in current_app.config['SUPPORTED_LANGUAGES']]
    if language not in valid_langs:
        return api_error(f'Invalid language. Choose from: {", ".join(valid_langs[:10])}...')

    snippet = Snippet(
        title=title, body=body, language=language,
        description=description, is_public=is_public,
        user_id=current_user.id
    )

    tag_names = parse_tags(tags_raw)
    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, slug=slugify(tag_name))
            db.session.add(tag)
        snippet.tags.append(tag)

    db.session.add(snippet)
    db.session.commit()

    return api_success(snippet_to_dict(snippet), 201)


# ─── Update Snippet (API) ───────────────────────────────────────────
@api_bp.route('/snippets/<int:id>', methods=['PUT'])
@login_required
def update_snippet(id):
    snippet = Snippet.query.get_or_404(id)
    if snippet.user_id != current_user.id:
        abort(403)

    data = request.get_json()
    if not data:
        return api_error('JSON body required')

    if 'title' in data:
        snippet.title = data['title'].strip()
    if 'body' in data:
        snippet.body = data['body']
    if 'language' in data:
        snippet.language = data['language']
    if 'description' in data:
        snippet.description = data['description'].strip()
    if 'is_public' in data:
        snippet.is_public = data['is_public']
    if 'tags' in data:
        tag_names = parse_tags(data['tags'])
        snippet.tags.clear()
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                db.session.add(tag)
            snippet.tags.append(tag)

    db.session.commit()
    return api_success(snippet_to_dict(snippet))


# ─── Delete Snippet (API) ───────────────────────────────────────────
@api_bp.route('/snippets/<int:id>', methods=['DELETE'])
@login_required
def delete_snippet(id):
    snippet = Snippet.query.get_or_404(id)
    if snippet.user_id != current_user.id:
        abort(403)

    db.session.delete(snippet)
    db.session.commit()
    return api_success({'deleted': True}, 200)


# ─── Like Toggle (API) ──────────────────────────────────────────────
@api_bp.route('/snippets/<int:id>/like', methods=['POST'])
@login_required
def toggle_like(id):
    snippet = Snippet.query.get_or_404(id)

    existing = Like.query.filter_by(user_id=current_user.id, snippet_id=id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return api_success({'liked': False, 'count': snippet.like_count})
    else:
        like = Like(user_id=current_user.id, snippet_id=id)
        db.session.add(like)
        db.session.commit()
        return api_success({'liked': True, 'count': snippet.like_count})


# ─── Get Tags ───────────────────────────────────────────────────────
@api_bp.route('/tags', methods=['GET'])
def list_tags():
    tags = Tag.query.join(
        tag_association, Tag.id == tag_association.c.tag_id
    ).join(Snippet).filter(
        Snippet.is_public == True
    ).group_by(Tag.id).order_by(
        db.func.count(Snippet.id).desc()
    ).all()

    return api_success({
        'tags': [{'name': t.name, 'slug': t.slug} for t in tags]
    })


# ─── Get User Profile (API) ─────────────────────────────────────────
@api_bp.route('/users/<username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return api_success({
        'id': user.id,
        'username': user.username,
        'bio': user.bio,
        'github_url': user.github_url,
        'website_url': user.website_url,
        'snippet_count': user.snippet_count,
        'total_likes_received': user.total_likes_received,
        'joined': user.created_at.isoformat(),
    })