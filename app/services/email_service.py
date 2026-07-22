"""
Email Service — Sends news notifications and transaction alerts via Gmail SMTP.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from flask import current_app
from app.models import NewsletterSubscription

logger = logging.getLogger(__name__)


def _site_url() -> str:
    """Get the base site URL from config, stripping trailing slash."""
    return current_app.config.get('SITE_URL', 'http://localhost:5000').rstrip('/')


def send_email(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    """
    Reusable helper function to send emails using SMTP with TLS encryption.

    Args:
        to_email: Recipient email address.
        subject: The subject line of the email.
        html_body: The HTML rendered body of the email.
        text_body: Optional plain text alternative for fallback.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    # Load configuration parameters safely from Flask application context
    server_host = current_app.config.get("SMTP_SERVER")
    port = current_app.config.get("SMTP_PORT", 587)
    username = current_app.config.get("SMTP_USERNAME")
    password = current_app.config.get("SMTP_PASSWORD")
    from_email = current_app.config.get("MAIL_FROM")
    from_name = current_app.config.get("MAIL_FROM_NAME", "CodeLab")

    if not all([server_host, port, username, password, from_email]):
        logger.error("SMTP Configuration is incomplete. Check config.py variables.")
        return False

    # Setup the multi-part email payload container
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email

    # Attach alternative structural blocks (Text goes first, HTML second)
    if text_body:
        message.attach(MIMEText(text_body, "plain", "utf-8"))
    
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        # Connect to server with a short timeout so failures don't hang requests
        server = smtplib.SMTP(server_host, port, timeout=10)
        server.starttls()
        server.login(username, password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        logger.warning(f"SMTP error while sending email to {to_email}: {e}")
        return False


def send_welcome_email(email: str) -> bool:
    """
    Send a welcome email to a new subscriber.

    Args:
        email: The recipient subscriber's email address string.
    """
    subject = "Welcome to CodeLab News!"
    base_url = _site_url()
    html_content = f'''
    <div style="max-width:600px;margin:0 auto;font-family:sans-serif;color:#1e293b;">
        <div style="background:#6366f1;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:24px;">CodeLab News</h1>
            <p style="color:#c7d2fe;margin:8px 0 0;">Your source for the latest in tech & coding</p>
        </div>
        <div style="padding:24px;background:#f8fafc;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;border-top:none;">
            <p style="font-size:16px;">Hello!</p>
            <p style="font-size:16px;">You've successfully subscribed to <strong>CodeLab News</strong>.</p>
            <p style="font-size:16px;">We'll send you the latest coding news, tech updates, and developer insights
            from Hacker News, Dev.to, and Reddit r/programming — summarized by AI.</p>
            <p style="font-size:16px;">Stay curious, stay coding!</p>
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">
            <p style="font-size:13px;color:#94a3b8;text-align:center;">
                You received this because you subscribed on CodeLab.<br>
                <a href="{base_url}/subscribe/unsubscribe?email={email}" style="color:#6366f1;">Unsubscribe</a>
            </p>
        </div>
    </div>
    '''
    
    success = send_email(to_email=email, subject=subject, html_body=html_content)
    if success:
        logger.info(f"Welcome email successfully sent to {email}")
    return success


def send_news_notifications(articles: List[Dict[str, Any]]) -> None:
    """
    Send compiled news digest email to all active subscribers.

    Args:
        articles: List of article dicts with title, summary, source, source_url.
    """
    if not articles:
        return

    subscribers = NewsletterSubscription.query.filter_by(is_active=True).all()
    if not subscribers:
        logger.info("No active subscribers to notify.")
        return

    # Build unique internal HTML structures for all structural changes
    articles_html = ''
    for article in articles:
        title = article.get('title', 'Untitled')
        summary = article.get('summary', '')
        source = article.get('source', '').title()
        source_url = article.get('source_url', '#')
        if not summary:
            summary = title

        source_colors = {
            'Hackernews': '#ff6600',
            'Devto': '#3b49df',
            'Reddit': '#ff4500',
        }
        badge_color = source_colors.get(source, '#6366f1')

        articles_html += f'''
        <div style="margin-bottom:16px;padding:16px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;">
            <span style="display:inline-block;background:{badge_color};color:#fff;font-size:11px;padding:2px 8px;border-radius:4px;margin-bottom:8px;">
                {source}
            </span>
            <h3 style="margin:0 0 6px;font-size:16px;">
                <a href="{source_url}" style="color:#1e293b;text-decoration:none;">{title}</a>
            </h3>
            <p style="margin:0;color:#475569;font-size:14px;line-height:1.5;">{summary}</p>
        </div>
        '''

    base_url = _site_url()

    email_html = f'''
    <div style="max-width:600px;margin:0 auto;font-family:sans-serif;color:#1e293b;">
        <div style="background:#6366f1;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:24px;">CodeLab News</h1>
            <p style="color:#c7d2fe;margin:8px 0 0;">{len(articles)} new articles just in</p>
        </div>
        <div style="padding:24px;background:#f8fafc;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;border-top:none;">
            {articles_html}
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">
            <p style="font-size:13px;color:#94a3b8;text-align:center;">
                Brought to you by CodeLab — Code Snippet Sharing & Playground<br>
                <a href="{base_url}/news" style="color:#6366f1;">View all news on CodeLab</a>
            </p>
        </div>
    </div>
    '''

    subject = f'CodeLab News — {len(articles)} new tech articles'

    # Send structured updates to each active recipient loop safely
    for sub in subscribers:
        # Provide targeted unsubscribe tracking injection
        personalized_html = email_html + f'''
        <div style="padding:0 24px 24px;background:#f8fafc;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;border-top:none;margin-top:-24px;text-align:center;">
            <p style="font-size:13px;color:#94a3b8;margin:0;">
                <a href="{base_url}/subscribe/unsubscribe?email={sub.email}" style="color:#6366f1;">Unsubscribe from this list</a>
            </p>
        </div>
        '''
        
        success = send_email(to_email=sub.email, subject=subject, html_body=personalized_html)
        if success:
            logger.info(f"News email sent successfully to {sub.email}")
        else:
            logger.error(f"Failed to dispatch news email directly to {sub.email}")