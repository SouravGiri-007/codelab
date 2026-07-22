import traceback
from flask import current_app
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from werkzeug.exceptions import NotFound, Forbidden
from flask_wtf.csrf import CSRFError

errors = Blueprint('errors', __name__)


def _api_error(message, status):
    """Return a consistent JSON error envelope matching the API v1 format."""
    return jsonify({'success': False, 'error': message}), status


@errors.app_errorhandler(404)
def not_found_error(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _api_error('Not found', 404)
    return render_template('errors/404.html'), 404


@errors.app_errorhandler(403)
def forbidden_error(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _api_error('Forbidden', 403)
    return render_template('errors/403.html'), 403


@errors.app_errorhandler(500)
def internal_error(error):
    current_app.logger.exception("Unhandled exception", exc_info=error)
    traceback.print_exc()

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _api_error("Internal server error", 500)

    return render_template("errors/500.html"), 500


@errors.app_errorhandler(413)
def request_entity_too_large(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _api_error('Request too large', 413)
    flash('Your submission is too large. Please reduce the content size.', 'danger')
    return redirect(request.referrer or url_for('main.index'))


@errors.app_errorhandler(CSRFError)
def csrf_error(error):
    """Handle CSRF token validation failures gracefully."""
    current_app.logger.warning(f'CSRF validation failed: {error.description}')
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _api_error('Session expired. Please refresh and try again.', 400)
    flash('Your session has expired. Please try again.', 'danger')
    return redirect(request.referrer or url_for('main.index'))