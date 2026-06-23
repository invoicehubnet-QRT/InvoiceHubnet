"""
Error Handlers
==============
Custom error pages for 404, 500, and other HTTP errors.
"""

from flask import Blueprint, render_template
from flask_login import current_user

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def error_404(error):
    """404 Not Found error page."""
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(403)
def error_403(error):
    """403 Forbidden error page."""
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(500)
def error_500(error):
    """500 Internal Server Error page."""
    return render_template('errors/500.html'), 500

@errors_bp.app_errorhandler(429)
def error_429(error):
    """429 Too Many Requests error page."""
    return render_template('errors/429.html'), 429

@errors_bp.app_errorhandler(400)
def error_400(error):
    """400 Bad Request error page."""
    return render_template('errors/400.html'), 400