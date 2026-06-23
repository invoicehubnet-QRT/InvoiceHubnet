"""
Subscription Model
==================
Handles subscription plans and user subscriptions.
"""

from datetime import datetime
from enum import Enum
from app import db

class SubscriptionPlan(str, Enum):
    """Available subscription plan types."""
    FREE = 'free'
    BASIC = 'basic'
    PRIME = 'prime'
    FULL_SUITE = 'full_suite'

class Subscription(db.Model):
    """Subscription model linking users to their plans."""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    plan = db.Column(db.String(20), nullable=False, default=SubscriptionPlan.FREE.value)
    status = db.Column(db.String(20), nullable=False, default='active')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, default=True)
    payment_gateway = db.Column(db.String(20))  # flutterwave, stripe
    gateway_subscription_id = db.Column(db.String(255))
    gateway_customer_id = db.Column(db.String(255))
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def invoices_per_week(self):
        """Return the number of invoices allowed per week based on plan."""
        limits = {
            SubscriptionPlan.FREE.value: 1,
            SubscriptionPlan.BASIC.value: 2,
            SubscriptionPlan.PRIME.value: 4,
            SubscriptionPlan.FULL_SUITE.value: 7
        }
        return limits.get(self.plan, 1)
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    @property
    def days_until_expiry(self):
        """Calculate days until subscription expires."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def to_dict(self):
        """Convert subscription to dictionary."""
        return {
            'id': self.id,
            'plan': self.plan,
            'status': self.status,
            'is_active': self.is_active,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'invoices_per_week': self.invoices_per_week
        }