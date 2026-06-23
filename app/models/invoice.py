"""
Invoice Model
=============
Handles invoice creation and management.
"""

from datetime import datetime
from enum import Enum
from app import db

class InvoiceStatus(str, Enum):
    """Invoice status types."""
    DRAFT = 'draft'
    PENDING = 'pending'
    PAID = 'paid'
    CANCELLED = 'cancelled'
    OVERDUE = 'overdue'

class Currency(str, Enum):
    """Supported currencies."""
    NGN = 'NGN'  # Nigerian Naira
    USD = 'USD'  # US Dollar
    EUR = 'EUR'  # Euro
    GBP = 'GBP'  # British Pound
    KES = 'KES'  # Kenyan Shilling
    ZAR = 'ZAR'  # South African Rand
    GHS = 'GHS'  # Ghanaian Cedi

class Invoice(db.Model):
    """Invoice model for generating and managing invoices."""
    
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    
    # Invoice details
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default=Currency.NGN.value)
    status = db.Column(db.String(20), nullable=False, default=InvoiceStatus.DRAFT.value)
    
    # Totals
    subtotal = db.Column(db.Float, default=0.0)
    discount_percent = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    shipping_amount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)
    balance_due = db.Column(db.Float, default=0.0)
    
    # Payment info
    payment_gateway = db.Column(db.String(20))
    payment_reference = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime)
    
    # Notes and terms
    notes = db.Column(db.Text)
    terms = db.Column(db.Text)
    
    # Metadata
    is_sent = db.Column(db.Boolean, default=False)
    is_viewed = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    viewed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def calculate_totals(self):
        """Recalculate all invoice totals based on items."""
        self.subtotal = sum(item.total for item in self.items)
        self.discount_amount = self.subtotal * (self.discount_percent / 100)
        self.tax_amount = (self.subtotal - self.discount_amount) * (self.tax_percent / 100)
        self.total = self.subtotal - self.discount_amount + self.tax_amount + self.shipping_amount
        self.balance_due = self.total - self.amount_paid
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        if self.status == InvoiceStatus.PAID.value:
            return False
        return self.due_date < datetime.utcnow().date()
    
    @property
    def formatted_total(self):
        """Format total with currency symbol."""
        symbols = {
            Currency.NGN.value: '₦',
            Currency.USD.value: '$',
            Currency.EUR.value: '€',
            Currency.GBP.value: '£',
            Currency.KES.value: 'KSh',
            Currency.ZAR.value: 'R',
            Currency.GHS.value: '₵'
        }
        symbol = symbols.get(self.currency, '₦')
        return f"{symbol}{self.total:,.2f}"
    
    @property
    def days_until_due(self):
        """Calculate days until due date."""
        delta = self.due_date - datetime.utcnow().date()
        return delta.days
    
    def to_dict(self):
        """Convert invoice to dictionary."""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'currency': self.currency,
            'status': self.status,
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'tax_amount': self.tax_amount,
            'shipping_amount': self.shipping_amount,
            'total': self.total,
            'amount_paid': self.amount_paid,
            'balance_due': self.balance_due,
            'formatted_total': self.formatted_total,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class InvoiceItem(db.Model):
    """Individual line items within an invoice."""
    
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0)
    total = db.Column(db.Float, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_total(self):
        """Calculate item total."""
        self.total = self.quantity * self.unit_price
    
    def to_dict(self):
        """Convert item to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total': self.total
        }
    
    def __repr__(self):
        return f'<InvoiceItem {self.name}>'