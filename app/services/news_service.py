"""
News Service — Fetches coding/tech news from Hacker News, Dev.to, and Reddit r/programming.
"""
import logging
import re
import httpx
from flask import current_app
from app import db
from app.models import NewsArticle

logger = logging.getLogger(__name__)

# Realistic browser User-Agent to avoid being blocked by API providers
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'


def extract_text_from_html(html):
    """Strip HTML tags and extract clean readable text."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    for ent, ch in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'"), ('&apos;', "'")]:
        text = text.replace(ent, ch)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def fetch_article_content(url):
    """Fetch and extract plain text content from an article URL."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={'User-Agent': USER_AGENT})
            resp.raise_for_status()
            text = extract_text_from_html(resp.text)
            return text[:5000]
    except Exception as e:
        logger.warning(f"Failed to fetch content from {url[:80]}: {e}")
        return ''


async def fetch_hacker_news(max_items=10):
    """Fetch top stories from Hacker News API."""
    articles = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Get top story IDs
            resp = await client.get(
                'https://hacker-news.firebaseio.com/v0/topstories.json',
                headers={'User-Agent': USER_AGENT}
            )
            resp.raise_for_status()
            story_ids = resp.json()[:50]  # Get top 50, filter later

            # Fetch each story
            for sid in story_ids:
                if len(articles) >= max_items:
                    break
                try:
                    item_resp = await client.get(
                        f'https://hacker-news.firebaseio.com/v0/item/{sid}.json',
                        headers={'User-Agent': USER_AGENT}
                    )
                    item_resp.raise_for_status()
                    item = item_resp.json()

                    if not item or item.get('type') != 'story':
                        continue
                    if not item.get('url'):
                        continue

                    # Filter for tech/coding relevance
                    title = item.get('title', '')
                    # Score basic relevance by keywords
                    tech_keywords = ['code', 'programming', 'developer', 'software',
                                     'api', 'open source', 'language', 'framework',
                                     'database', 'ai', 'machine learning', 'python',
                                     'javascript', 'rust', 'golang', 'linux', 'devops',
                                     'security', 'web', 'app', 'data', 'algorithm',
                                     'release', 'update', 'version', 'tool', 'library']
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in tech_keywords):
                        # Accept top 10 even without keyword match
                        if len(articles) >= 3:
                            continue

                    articles.append({
                        'title': title,
                        'source': 'hackernews',
                        'source_url': item.get('url', ''),
                        'external_id': str(item.get('id', '')),
                        'summary': '',
                        'image_url': '',
                        'upvotes': item.get('score', 0),
                        'comment_count': item.get('descendants', 0),
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch HN story {sid}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to fetch Hacker News: {e}")

    return articles


async def fetch_devto(max_items=10):
    """Fetch top articles from Dev.to API."""
    articles = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                'https://dev.to/api/articles',
                params={'per_page': max_items, 'top': '7'},  # top this week
                headers={'User-Agent': USER_AGENT}
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data:
                articles.append({
                    'title': item.get('title', ''),
                    'source': 'devto',
                    'source_url': item.get('url', '') or item.get('canonical_url', ''),
                    'external_id': str(item.get('id', '')),
                    'summary': '',
                    'image_url': item.get('cover_image', '') or '',
                    'upvotes': item.get('positive_reactions_count', 0),
                    'comment_count': item.get('comments_count', 0),
                })

        except Exception as e:
            logger.error(f"Failed to fetch Dev.to: {e}")

    return articles


async def fetch_reddit(max_items=10):
    """Fetch hot posts from Reddit r/programming."""
    articles = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                'https://www.reddit.com/r/programming/hot.json',
                params={'limit': max_items},
                headers={
                    'User-Agent': USER_AGENT,
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            resp.raise_for_status()
            data = resp.json()

            for child in data.get('data', {}).get('children', []):
                item = child.get('data', {})
                url = item.get('url', '')
                # Skip self-posts (reddit links)
                if 'reddit.com' in url:
                    continue

                articles.append({
                    'title': item.get('title', ''),
                    'source': 'reddit',
                    'source_url': url,
                    'external_id': item.get('name', ''),
                    'summary': '',
                    'image_url': item.get('thumbnail', '') if item.get('thumbnail', '').startswith('http') else '',
                    'upvotes': item.get('score', 0),
                    'comment_count': item.get('num_comments', 0),
                })

        except Exception as e:
            logger.warning(f"Reddit fetch failed (non-critical): {e}")

    return articles


async def fetch_all_news():
    """Fetch news from all configured sources."""
    max_per = current_app.config.get('NEWS_MAX_PER_FETCH', 5)
    sources = current_app.config.get('NEWS_SOURCES', ['hackernews', 'devto', 'reddit'])

    all_articles = []

    if 'hackernews' in sources:
        all_articles.extend(await fetch_hacker_news(max_per))
    if 'devto' in sources:
        all_articles.extend(await fetch_devto(max_per))
    if 'reddit' in sources:
        all_articles.extend(await fetch_reddit(max_per))

    return all_articles


def deduplicate_articles(articles):
    """Remove articles with URLs already in the database."""
    new_articles = []
    try:
        existing_urls = set(
            url for (url,) in db.session.query(NewsArticle.source_url).all()
        )
    except Exception as e:
        logger.warning(f"Could not query existing URLs (connection issue?): {e}")
        db.session.rollback()
        # If DB is unavailable, accept all articles as new
        return articles

    for article in articles:
        if article['source_url'] not in existing_urls:
            new_articles.append(article)
            existing_urls.add(article['source_url'])

    return new_articles


def save_articles(articles):
    """Save fetched articles to the database."""
    saved_count = 0
    for article in articles:
        try:
            news = NewsArticle(
                title=article['title'][:300],
                source=article['source'],
                source_url=article['source_url'][:1000],
                external_id=article.get('external_id', ''),
                summary=article.get('summary', ''),
                image_url=article.get('image_url', '')[:1000],
                upvotes=article.get('upvotes', 0),
                comment_count=article.get('comment_count', 0),
                is_published=True,
            )
            db.session.add(news)
            saved_count += 1
        except Exception as e:
            logger.warning(f"Failed to save article '{article.get('title', '')[:50]}': {e}")

    if saved_count > 0:
        db.session.commit()
    return saved_count


async def run_news_fetch():
    """
    Main task: fetch news from sources, deduplicate, save.
    Called by the scheduler.
    """
    from app.services.ai_service import summarize_news

    try:
        logger.info("Starting news fetch...")
        articles = await fetch_all_news()
        logger.info(f"Fetched {len(articles)} raw articles")

        # Deduplicate against DB
        new_articles = deduplicate_articles(articles)
        logger.info(f"After dedup: {len(new_articles)} new articles")

        if not new_articles:
            return 0

        # Summarize each article with AI
        for article in new_articles:
            try:
                # Fetch article content if not already present
                content = article.get('content', '') or ''
                if not content.strip():
                    content = await fetch_article_content(article['source_url'])
                summary = summarize_news(article['title'], content)
                if summary:
                    article['summary'] = summary
            except Exception as e:
                logger.warning(f"Failed to summarize: {e}")

        # Save to DB
        count = save_articles(new_articles)
        logger.info(f"Saved {count} new articles")

        # Send email notifications
        if count > 0:
            from app.services.email_service import send_news_notifications
            send_news_notifications(new_articles)

        return count

    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        db.session.rollback()
        return 0