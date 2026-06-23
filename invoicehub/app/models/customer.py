"""
Customer Model
==============
Handles customer/client management.
"""

from datetime import datetime
from app import db

class Customer(db.Model):
    """Customer model for managing client information."""
    
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Nigeria')
    tax_id = db.Column(db.String(50))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    total_invoiced = db.Column(db.Float, default=0.0)
    total_paid = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='customer', lazy=True)
    company = db.relationship('Company', backref='customers')
    
    @property
    def outstanding_balance(self):
        """Calculate outstanding balance for this customer."""
        return self.total_invoiced - self.total_paid
    
    def to_dict(self):
        """Convert customer to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'total_invoiced': self.total_invoiced,
            'total_paid': self.total_paid,
            'outstanding_balance': self.outstanding_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Customer {self.name}>'