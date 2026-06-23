"""
Activity Log Model
==================
Tracks user activities for audit and analytics.
"""

from datetime import datetime
from enum import Enum
from app import db

class ActivityType(str, Enum):
    """Types of user activities to track."""
    LOGIN = 'login'
    LOGOUT = 'logout'
    REGISTER = 'register'
    INVOICE_CREATED = 'invoice_created'
    INVOICE_VIEWED = 'invoice_viewed'
    INVOICE_SENT = 'invoice_sent'
    INVOICE_PAID = 'invoice_paid'
    INVOICE_CANCELLED = 'invoice_cancelled'
    CUSTOMER_CREATED = 'customer_created'
    CUSTOMER_UPDATED = 'customer_updated'
    COMPANY_CREATED = 'company_created'
    COMPANY_UPDATED = 'company_updated'
    SUBSCRIPTION_CREATED = 'subscription_created'
    SUBSCRIPTION_UPDATED = 'subscription_updated'
    PAYMENT_INITIATED = 'payment_initiated'
    PAYMENT_COMPLETED = 'payment_completed'
    PASSWORD_RESET_REQUESTED = 'password_reset_requested'
    PROFILE_UPDATED = 'profile_updated'

class ActivityLog(db.Model):
    """Activity log model for tracking user actions."""
    
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    metadata = db.Column(db.Text)  # JSON data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert activity log to dictionary."""
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def log(user_id, activity_type, description=None, ip_address=None, 
            user_agent=None, metadata=None):
        """Create a new activity log entry."""
        log_entry = ActivityLog(
            user_id=user_id,
            activity_type=activity_type.value if isinstance(activity_type, ActivityType) else activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def __repr__(self):
        return f'<ActivityLog {self.activity_type}>'