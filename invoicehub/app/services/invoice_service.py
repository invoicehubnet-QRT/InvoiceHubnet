"""
Invoice Service
===============
Handles invoice business logic.
"""

from datetime import datetime, timedelta
from app import db
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.models.activity_log import ActivityLog, ActivityType

class InvoiceService:
    """Service for managing invoices."""
    
    @staticmethod
    def generate_invoice_number(user_id):
        """Generate a unique invoice number."""
        year = datetime.utcnow().year
        prefix = f"INV-{year}"
        
        # Get the last invoice number for this user
        last_invoice = Invoice.query.filter(
            Invoice.user_id == user_id,
            Invoice.invoice_number.like(f'{prefix}%')
        ).order_by(Invoice.id.desc()).first()
        
        if last_invoice:
            # Extract the sequence number and increment
            try:
                seq = int(last_invoice.invoice_number.split('-')[-1])
                new_seq = seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1
        
        return f"{prefix}-{new_seq:04d}"
    
    @staticmethod
    def create_invoice(user, data, company=None):
        """
        Create a new invoice.
        
        Args:
            user: User object
            data: Invoice data dictionary
            company: Company object (optional)
        
        Returns:
            Invoice: Created invoice object
        """
        invoice = Invoice(
            user_id=user.id,
            company_id=company.id if company else None,
            customer_id=data.get('customer_id'),
            invoice_number=InvoiceService.generate_invoice_number(user.id),
            invoice_date=data.get('invoice_date', datetime.utcnow().date()),
            due_date=data.get('due_date', datetime.utcnow().date() + timedelta(days=30)),
            currency=data.get('currency', 'NGN'),
            status=data.get('status', InvoiceStatus.DRAFT.value),
            notes=data.get('notes'),
            terms=data.get('terms'),
            discount_percent=data.get('discount_percent', 0),
            tax_percent=data.get('tax_percent', 0),
            shipping_amount=data.get('shipping_amount', 0)
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get the invoice ID
        
        # Add invoice items
        items_data = data.get('items', [])
        for item_data in items_data:
            item = InvoiceItem(
                invoice_id=invoice.id,
                name=item_data.get('name', ''),
                description=item_data.get('description', ''),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', 0)
            )
            item.calculate_total()
            db.session.add(item)
        
        # Calculate totals
        invoice.calculate_totals()
        db.session.commit()
        
        # Log activity
        ActivityLog.log(
            user_id=user.id,
            activity_type=ActivityType.INVOICE_CREATED,
            description=f'Invoice {invoice.invoice_number} created',
            metadata={'invoice_id': invoice.id}
        )
        
        return invoice
    
    @staticmethod
    def update_invoice(invoice, data):
        """Update an existing invoice."""
        # Update basic fields
        if 'customer_id' in data:
            invoice.customer_id = data['customer_id']
        if 'invoice_date' in data:
            invoice.invoice_date = data['invoice_date']
        if 'due_date' in data:
            invoice.due_date = data['due_date']
        if 'currency' in data:
            invoice.currency = data['currency']
        if 'status' in data:
            invoice.status = data['status']
        if 'notes' in data:
            invoice.notes = data['notes']
        if 'terms' in data:
            invoice.terms = data['terms']
        if 'discount_percent' in data:
            invoice.discount_percent = data['discount_percent']
        if 'tax_percent' in data:
            invoice.tax_percent = data['tax_percent']
        if 'shipping_amount' in data:
            invoice.shipping_amount = data['shipping_amount']
        
        # Update items if provided
        if 'items' in data:
            # Remove existing items
            InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
            
            # Add new items
            for item_data in data['items']:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    name=item_data.get('name', ''),
                    description=item_data.get('description', ''),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', 0)
                )
                item.calculate_total()
                db.session.add(item)
        
        # Recalculate totals
        invoice.calculate_totals()
        db.session.commit()
        
        return invoice
    
    @staticmethod
    def mark_as_sent(invoice):
        """Mark an invoice as sent."""
        invoice.is_sent = True
        invoice.sent_at = datetime.utcnow()
        if invoice.status == InvoiceStatus.DRAFT.value:
            invoice.status = InvoiceStatus.PENDING.value
        db.session.commit()
        
        ActivityLog.log(
            user_id=invoice.user_id,
            activity_type=ActivityType.INVOICE_SENT,
            description=f'Invoice {invoice.invoice_number} marked as sent',
            metadata={'invoice_id': invoice.id}
        )
    
    @staticmethod
    def mark_as_paid(invoice, amount=None, payment_gateway=None, payment_reference=None):
        """Mark an invoice as paid."""
        payment_amount = amount or invoice.total
        invoice.amount_paid = payment_amount
        invoice.balance_due = invoice.total - payment_amount
        invoice.status = InvoiceStatus.PAID.value
        invoice.paid_at = datetime.utcnow()
        
        if payment_gateway:
            invoice.payment_gateway = payment_gateway
        if payment_reference:
            invoice.payment_reference = payment_reference
        
        # Update customer totals
        if invoice.customer:
            invoice.customer.total_paid += payment_amount
        
        db.session.commit()
        
        ActivityLog.log(
            user_id=invoice.user_id,
            activity_type=ActivityType.INVOICE_PAID,
            description=f'Invoice {invoice.invoice_number} marked as paid',
            metadata={'invoice_id': invoice.id, 'amount': payment_amount}
        )
    
    @staticmethod
    def mark_as_cancelled(invoice):
        """Mark an invoice as cancelled."""
        invoice.status = InvoiceStatus.CANCELLED.value
        db.session.commit()
        
        ActivityLog.log(
            user_id=invoice.user_id,
            activity_type=ActivityType.INVOICE_CANCELLED,
            description=f'Invoice {invoice.invoice_number} cancelled',
            metadata={'invoice_id': invoice.id}
        )
    
    @staticmethod
    def mark_as_viewed(invoice):
        """Mark an invoice as viewed."""
        if not invoice.is_viewed:
            invoice.is_viewed = True
            invoice.viewed_at = datetime.utcnow()
            db.session.commit()
            
            ActivityLog.log(
                user_id=invoice.user_id,
                activity_type=ActivityType.INVOICE_VIEWED,
                description=f'Invoice {invoice.invoice_number} viewed',
                metadata={'invoice_id': invoice.id}
            )
    
    @staticmethod
    def get_invoices_by_status(user_id, status):
        """Get all invoices for a user with a specific status."""
        return Invoice.query.filter_by(
            user_id=user_id,
            status=status
        ).order_by(Invoice.created_at.desc()).all()
    
    @staticmethod
    def get_overdue_invoices(user_id):
        """Get all overdue invoices for a user."""
        return Invoice.query.filter(
            Invoice.user_id == user_id,
            Invoice.status == InvoiceStatus.PENDING.value,
            Invoice.due_date < datetime.utcnow().date()
        ).order_by(Invoice.due_date.asc()).all()
    
    @staticmethod
    def get_recent_invoices(user_id, limit=5):
        """Get recent invoices for a user."""
        return Invoice.query.filter_by(
            user_id=user_id
        ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_invoice_stats(user_id):
        """Get invoice statistics for a user."""
        invoices = Invoice.query.filter_by(user_id=user_id).all()
        
        total_invoices = len(invoices)
        draft_count = len([i for i in invoices if i.status == InvoiceStatus.DRAFT.value])
        pending_count = len([i for i in invoices if i.status == InvoiceStatus.PENDING.value])
        paid_count = len([i for i in invoices if i.status == InvoiceStatus.PAID.value])
        cancelled_count = len([i for i in invoices if i.status == InvoiceStatus.CANCELLED.value])
        
        total_revenue = sum(i.total for i in invoices if i.status == InvoiceStatus.PAID.value)
        outstanding_amount = sum(i.balance_due for i in invoices if i.status == InvoiceStatus.PENDING.value)
        
        return {
            'total_invoices': total_invoices,
            'draft_count': draft_count,
            'pending_count': pending_count,
            'paid_count': paid_count,
            'cancelled_count': cancelled_count,
            'total_revenue': total_revenue,
            'outstanding_amount': outstanding_amount
        }