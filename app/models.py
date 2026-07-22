from datetime import datetime, timezone
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)  # Nullable for Google-only users
    bio = db.Column(db.String(500), default='')
    avatar_url = db.Column(db.String(500), default='')
    github_url = db.Column(db.String(200), default='')
    website_url = db.Column(db.String(200), default='')
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    auth_provider = db.Column(db.String(20), default='local')  # 'local', 'google', 'both'

    # Relationships
    snippets = db.relationship('Snippet', backref='author', lazy='dynamic',
                               cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic',
                               cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic',
                            cascade='all, delete-orphan')
    saved_snippets = db.relationship('SavedSnippet', backref='user', lazy='dynamic',
                                     cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')

    @property
    def snippet_count(self):
        return self.snippets.count()

    @property
    def total_likes_received(self):
        return Like.query.join(Snippet).filter(Snippet.user_id == self.id).count()

    def __repr__(self):
        return f'<User {self.username}>'


tag_association = db.Table(
    'snippet_tags',
    db.Column('snippet_id', db.Integer, db.ForeignKey('snippets.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


class Snippet(db.Model):
    __tablename__ = 'snippets'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(30), nullable=False, index=True)
    description = db.Column(db.Text, default='')
    is_public = db.Column(db.Boolean, default=True)
    is_playground = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    comments = db.relationship('Comment', backref='snippet', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='Comment.created_at')
    likes = db.relationship('Like', backref='snippet', lazy='dynamic',
                            cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=tag_association,
                           backref=db.backref('snippets', lazy='dynamic'), lazy='joined')

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    @property
    def is_saved_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return SavedSnippet.query.filter_by(
            user_id=user.id, snippet_id=self.id
        ).first() is not None

    def __repr__(self):
        return f'<Snippet {self.title}>'


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(30), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Tag {self.name}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    snippet_id = db.Column(db.Integer, db.ForeignKey('snippets.id'), nullable=False)

    def __repr__(self):
        return f'<Comment by {self.author.username} on {self.snippet.title}>'


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    snippet_id = db.Column(db.Integer, db.ForeignKey('snippets.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'snippet_id', name='unique_like'),)


class SavedSnippet(db.Model):
    __tablename__ = 'saved_snippets'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    snippet_id = db.Column(db.Integer, db.ForeignKey('snippets.id'), nullable=False)

    snippet = db.relationship('Snippet', backref=db.backref('saves', cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('user_id', 'snippet_id', name='unique_save'),)


# ─── News ─────────────────────────────────────────────────────────────

class NewsArticle(db.Model):
    __tablename__ = 'news_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    source = db.Column(db.String(50), nullable=False, index=True)  # hackernews, devto, reddit
    source_url = db.Column(db.String(1000), unique=True, nullable=False)
    external_id = db.Column(db.String(100), default='')  # HN id, Dev.to id, Reddit id
    summary = db.Column(db.Text, default='')
    image_url = db.Column(db.String(1000), default='')
    category = db.Column(db.String(50), default='general')
    upvotes = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    fetched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<NewsArticle {self.title[:50]}>'


# ─── Newsletter Subscription ──────────────────────────────────────────

class NewsletterSubscription(db.Model):
    __tablename__ = 'newsletter_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    unsubscribed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<NewsletterSubscription {self.email}>'


# ─── AI Chat ──────────────────────────────────────────────────────────

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ChatMessage {self.role} by user {self.user_id}>'


# ─── Admin Settings ───────────────────────────────────────────────────

class AdminSetting(db.Model):
    __tablename__ = 'admin_settings'

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(500), default='')

    def __repr__(self):
        return f'<AdminSetting {self.key}={self.value}>'