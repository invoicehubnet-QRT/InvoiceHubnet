"""
User Model
==========
Handles user authentication and profile management.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    subscription = db.relationship('Subscription', backref='user', uselist=False, lazy=True)
    companies = db.relationship('Company', backref='owner', lazy=True, cascade='all, delete-orphan')
    customers = db.relationship('Customer', backref='user', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='user', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    password_resets = db.relationship('PasswordReset', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def initials(self):
        """Return user's initials for avatar."""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    
    def get_subscription_plan(self):
        """Get the user's current subscription plan."""
        if self.subscription:
            return self.subscription.plan
        return 'free'
    
    def get_company(self):
        """Get the user's primary company."""
        return Company.query.filter_by(user_id=self.id, is_primary=True).first()
    
    def can_create_invoice(self):
        """Check if user can create more invoices this week."""
        if not self.subscription:
            return True  # Free plan - 1 invoice per week
        
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Count invoices created in the last 7 days
        invoice_count = Invoice.query.filter(
            Invoice.user_id == self.id,
            Invoice.created_at >= week_ago
        ).count()
        
        return invoice_count < self.subscription.invoices_per_week
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'avatar': self.avatar,
            'is_verified': self.is_verified,
            'subscription_plan': self.get_subscription_plan(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def generate_verification_token(self):
        """Generate a unique email verification token."""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token
    
    def __repr__(self):
        return f'<User {self.email}>'