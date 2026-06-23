"""
Password Reset Model
====================
Handles password reset tokens and requests.
"""

from datetime import datetime, timedelta
from secrets import token_urlsafe
from app import db

class PasswordReset(db.Model):
    """Password reset model for handling reset requests."""
    
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_token(user_id, ip_address=None):
        """Generate a new password reset token."""
        # Invalidate any existing tokens
        PasswordReset.query.filter_by(user_id=user_id, used=False).update({'used': True})
        
        # Create new token
        token = PasswordReset(
            user_id=user_id,
            token=token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ip_address=ip_address
        )
        db.session.add(token)
        db.session.commit()
        return token
    
    @staticmethod
    def verify_token(token):
        """Verify a password reset token."""
        reset = PasswordReset.query.filter_by(token=token, used=False).first()
        if not reset:
            return None
        if reset.expires_at < datetime.utcnow():
            return None
        return reset
    
    def mark_used(self):
        """Mark this token as used."""
        self.used = True
        db.session.commit()
    
    @property
    def is_valid(self):
        """Check if token is still valid."""
        return not self.used and self.expires_at > datetime.utcnow()
    
    def __repr__(self):
        return f'<PasswordReset {self.id}>'