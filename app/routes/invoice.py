"""
Invoice Routes
==============
Handles invoice creation, preview, and management.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus, Currency
from app.models.company import Company
from app.models.customer import Customer
from app.services.invoice_service import InvoiceService
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService

invoice_bp = Blueprint('invoice', __name__)

@invoice_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Invoice creation page."""
    # Get user's company and customers
    company = Company.query.filter_by(user_id=current_user.id, is_primary=True).first()
    customers = Customer.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Get next invoice number
    invoice_number = InvoiceService.generate_invoice_number(current_user.id)
    
    # Set default dates
    invoice_date = datetime.utcnow().date()
    due_date = invoice_date + timedelta(days=30)
    
    # Get currencies
    currencies = [c.value for c in Currency]
    
    if request.method == 'POST':
        # Process form data
        data = {
            'customer_id': request.form.get('customer_id'),
            'invoice_date': datetime.strptime(request.form.get('invoice_date'), '%Y-%m-%d').date() if request.form.get('invoice_date') else invoice_date,
            'due_date': datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else due_date,
            'currency': request.form.get('currency', 'NGN'),
            'notes': request.form.get('notes'),
            'terms': request.form.get('terms'),
            'discount_percent': float(request.form.get('discount_percent', 0) or 0),
            'tax_percent': float(request.form.get('tax_percent', 0) or 0),
            'shipping_amount': float(request.form.get('shipping_amount', 0) or 0),
            'items': []
        }
        
        # Parse items
        item_names = request.form.getlist('item_name')
        item_descriptions = request.form.getlist('item_description')
        item_quantities = request.form.getlist('item_quantity')
        item_prices = request.form.getlist('item_price')
        
        for i, name in enumerate(item_names):
            if name and name.strip():
                data['items'].append({
                    'name': name,
                    'description': item_descriptions[i] if i < len(item_descriptions) else '',
                    'quantity': float(item_quantities[i]) if i < len(item_quantities) and item_quantities[i] else 1,
                    'unit_price': float(item_prices[i]) if i < len(item_prices) and item_prices[i] else 0
                })
        
        # Create invoice
        invoice = InvoiceService.create_invoice(current_user, data, company)
        
        flash(f'Invoice {invoice.invoice_number} created successfully!', 'success')
        return redirect(url_for('invoice.preview', invoice_id=invoice.id))
    
    return render_template('invoice/create.html',
                         company=company,
                         customers=customers,
                         invoice_number=invoice_number,
                         invoice_date=invoice_date,
                         due_date=due_date,
                         currencies=currencies)

@invoice_bp.route('/preview/<int:invoice_id>')
@login_required
def preview(invoice_id):
    """Invoice preview page."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Ensure user owns this invoice
    if invoice.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    company = invoice.company
    customer = invoice.customer
    
    # Calculate totals
    invoice.calculate_totals()
    
    return render_template('invoice/preview.html',
                         invoice=invoice,
                         company=company,
                         customer=customer)

@invoice_bp.route('/edit/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def edit(invoice_id):
    """Invoice edit page."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    company = invoice.company
    customers = Customer.query.filter_by(user_id=current_user.id, is_active=True).all()
    currencies = [c.value for c in Currency]
    
    if request.method == 'POST':
        data = {
            'customer_id': request.form.get('customer_id'),
            'invoice_date': datetime.strptime(request.form.get('invoice_date'), '%Y-%m-%d').date() if request.form.get('invoice_date') else invoice.invoice_date,
            'due_date': datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else invoice.due_date,
            'currency': request.form.get('currency', invoice.currency),
            'status': request.form.get('status', invoice.status),
            'notes': request.form.get('notes'),
            'terms': request.form.get('terms'),
            'discount_percent': float(request.form.get('discount_percent', 0) or 0),
            'tax_percent': float(request.form.get('tax_percent', 0) or 0),
            'shipping_amount': float(request.form.get('shipping_amount', 0) or 0),
            'items': []
        }
        
        # Parse items
        item_names = request.form.getlist('item_name')
        item_descriptions = request.form.getlist('item_description')
        item_quantities = request.form.getlist('item_quantity')
        item_prices = request.form.getlist('item_price')
        
        for i, name in enumerate(item_names):
            if name and name.strip():
                data['items'].append({
                    'name': name,
                    'description': item_descriptions[i] if i < len(item_descriptions) else '',
                    'quantity': float(item_quantities[i]) if i < len(item_quantities) and item_quantities[i] else 1,
                    'unit_price': float(item_prices[i]) if i < len(item_prices) and item_prices[i] else 0
                })
        
        invoice = InvoiceService.update_invoice(invoice, data)
        
        flash(f'Invoice {invoice.invoice_number} updated successfully!', 'success')
        return redirect(url_for('invoice.preview', invoice_id=invoice.id))
    
    return render_template('invoice/edit.html',
                         invoice=invoice,
                         company=company,
                         customers=customers,
                         currencies=currencies)

@invoice_bp.route('/download/<int:invoice_id>')
@login_required
def download_pdf(invoice_id):
    """Download invoice as PDF."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Generate PDF
    pdf_data = PDFService.generate_invoice_pdf(invoice, current_user)
    
    filename = f"Invoice-{invoice.invoice_number}.pdf"
    
    return send_file(
        pdf_data,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@invoice_bp.route('/print/<int:invoice_id>')
@login_required
def print_invoice(invoice_id):
    """Print invoice page."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    company = invoice.company
    customer = invoice.customer
    
    return render_template('invoice/print.html',
                         invoice=invoice,
                         company=company,
                         customer=customer)

@invoice_bp.route('/send/<int:invoice_id>', methods=['POST'])
@login_required
def send_invoice(invoice_id):
    """Send invoice via email."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    recipient_email = request.form.get('email', '')
    
    if not recipient_email:
        return jsonify({'status': 'error', 'message': 'Email address is required'})
    
    # Send email with PDF attachment
    success = EmailService.send_invoice_email(current_user, invoice, recipient_email)
    
    if success:
        InvoiceService.mark_as_sent(invoice)
        return jsonify({'status': 'success', 'message': 'Invoice sent successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send email'})

@invoice_bp.route('/status/<int:invoice_id>', methods=['POST'])
@login_required
def update_status(invoice_id):
    """Update invoice status."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    new_status = request.json.get('status')
    
    if new_status == 'paid':
        InvoiceService.mark_as_paid(invoice)
    elif new_status == 'cancelled':
        InvoiceService.mark_as_cancelled(invoice)
    else:
        invoice.status = new_status
        db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Invoice marked as {new_status}'})

@invoice_bp.route('/delete/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    """Delete an invoice."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    invoice_number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Invoice {invoice_number} deleted'})