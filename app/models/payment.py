"""
Payment Model
=============
Handles payment transactions and history.
"""

from datetime import datetime
from enum import Enum
from app import db

class PaymentStatus(str, Enum):
    """Payment status types."""
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'

class PaymentGateway(str, Enum):
    """Supported payment gateways."""
    FLUTTERWAVE = 'flutterwave'
    STRIPE = 'stripe'

class Payment(db.Model):
    """Payment model for tracking transactions."""
    
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'))
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    
    gateway = db.Column(db.String(20), nullable=False)
    reference = db.Column(db.String(100))
    transaction_id = db.Column(db.String(100))
    
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='NGN')
    status = db.Column(db.String(20), nullable=False, default=PaymentStatus.PENDING.value)
    
    plan = db.Column(db.String(20))  # Plan being purchased
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    
    response_data = db.Column(db.Text)  # JSON response from gateway
    failure_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='payments')
    subscription = db.relationship('Subscription', backref='payments')
    invoice = db.relationship('Invoice', backref='payment')
    
    @property
    def is_successful(self):
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED.value
    
    def to_dict(self):
        """Convert payment to dictionary."""
        return {
            'id': self.id,
            'gateway': self.gateway,
            'reference': self.reference,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'plan': self.plan,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Payment {self.reference or self.id}>'