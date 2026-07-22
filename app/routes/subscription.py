"""Subscription routes — email newsletter subscribe/unsubscribe."""
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from app import db
from app.models import NewsletterSubscription
from app.forms import SubscribeForm
from datetime import datetime, timezone

sub_bp = Blueprint('subscribe', __name__)


@sub_bp.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Subscribe to the newsletter."""
    form = SubscribeForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        # Check for existing (maybe unsubscribed)
        existing = NewsletterSubscription.query.filter_by(email=email).first()
        if existing:
            if existing.is_active:
                flash('This email is already subscribed!', 'info')
                return redirect(url_for('subscribe.subscribe'))
            else:
                existing.is_active = True
                existing.unsubscribed_at = None
                db.session.commit()
        else:
            sub = NewsletterSubscription(email=email, is_active=True)
            db.session.add(sub)
            db.session.commit()

        # Send welcome email in a background thread (with app context for SMTP config)
        import threading
        _app = current_app._get_current_object()

        def _send_welcome_async(app, subscriber_email):
            with app.app_context():
                try:
                    from app.services.email_service import send_welcome_email
                    send_welcome_email(subscriber_email)
                except Exception:
                    pass

        threading.Thread(
            target=_send_welcome_async, args=(_app, email), daemon=True
        ).start()

        flash('Successfully subscribed to CodeLab News!', 'success')
        return redirect(url_for('subscribe.subscribe'))

    return render_template('subscription/subscribe.html', form=form)


@sub_bp.route('/subscribe/unsubscribe')
def unsubscribe():
    """Unsubscribe from the newsletter via email link."""
    email = request.args.get('email', '').strip().lower()
    if not email:
        flash('No email provided for unsubscribe.', 'danger')
        return redirect(url_for('subscribe.subscribe'))

    sub = NewsletterSubscription.query.filter_by(email=email).first()
    if sub:
        sub.is_active = False
        sub.unsubscribed_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('You have been unsubscribed from CodeLab News.', 'info')
    else:
        flash('That email was not found in our subscribers list.', 'info')

    return redirect(url_for('subscribe.subscribe'))