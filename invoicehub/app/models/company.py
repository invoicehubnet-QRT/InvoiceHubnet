"""
Company Model
=============
Handles company/business profiles for users.
"""

from datetime import datetime
from app import db

class Company(db.Model):
    """Company model for user business profiles."""
    
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(255))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Nigeria')
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    website = db.Column(db.String(255))
    tax_id = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    account_name = db.Column(db.String(100))
    payment_instructions = db.Column(db.Text)
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='company', lazy=True)
    
    def to_dict(self):
        """Convert company to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'tax_id': self.tax_id,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_name': self.account_name,
            'payment_instructions': self.payment_instructions,
            'is_primary': self.is_primary
        }
    
    def __repr__(self):
        return f'<Company {self.name}>'