"""
InvoiceHubNet - Flask Application Factory
========================================
Cloud-based invoice generation platform for freelancers, startups, and businesses.
Built by Quick Red Tech Software Development Studio.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
compress = Compress()

def create_app(config_name=None):
    """
    Application factory for creating Flask app instances.
    
    Args:
        config_name: Configuration object or None for default
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'production')
    
    # Configure app
    app.config.from_object(f'app.config.{config_name.title()}Config')
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    compress.init_app(app)
    CORS(app, supports_credentials=True)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register user loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.invoice import invoice_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.customer import customer_bp
    from app.routes.subscription import subscription_bp
    from app.routes.payment import payment_bp
    from app.routes.api import api_bp
    from app.routes.profile import profile_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(invoice_bp, url_prefix='/invoice')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(customer_bp, url_prefix='/customers')
    app.register_blueprint(subscription_bp, url_prefix='/subscription')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    return app

def register_error_handlers(app):
    """Register custom error handlers for the application."""
    from app.routes.errors import errors_bp
    app.register_blueprint(errors_bp)

def register_context_processors(app):
    """Register template context processors."""
    @app.context_processor
    def inject_company():
        """Inject company information into all templates."""
        from app.models.company import Company
        return {
            'company_name': 'InvoiceHubNet',
            'company_tagline': 'Create Professional Invoices in Seconds.',
            'company_email': 'invoicehubnet@gmail.com',
            'company_url': 'https://invoicehubnet.vercel.app'
        }
    
    @app.context_processor
    def inject_subscription_plans():
        """Make subscription plans available in all templates."""
        from app.services.subscription_service import SUBSCRIPTION_PLANS
        return {'subscription_plans': SUBSCRIPTION_PLANS}

# Create application instance
app = create_app()