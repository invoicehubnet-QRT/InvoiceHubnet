"""
Routes Package Initialization
=============================
Export all route blueprints.
"""

from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.invoice import invoice_bp
from app.routes.dashboard import dashboard_bp
from app.routes.customer import customer_bp
from app.routes.subscription import subscription_bp
from app.routes.payment import payment_bp
from app.routes.api import api_bp
from app.routes.errors import errors_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'invoice_bp',
    'dashboard_bp',
    'customer_bp',
    'subscription_bp',
    'payment_bp',
    'api_bp',
    'errors_bp'
]