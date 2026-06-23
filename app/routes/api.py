"""
API Routes
==========
RESTful API endpoints for frontend integration.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.customer import Customer
from app.models.company import Company
from app.services.invoice_service import InvoiceService
from app.services.subscription_service import SubscriptionService

api_bp = Blueprint('api', __name__)

# ==================== Invoice API ====================

@api_bp.route('/invoices', methods=['GET'])
@login_required
def get_invoices():
    """Get all invoices for the current user."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Invoice.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'status': 'success',
        'data': [inv.to_dict() for inv in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })

@api_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@login_required
def get_invoice(invoice_id):
    """Get a specific invoice."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    return jsonify({
        'status': 'success',
        'data': invoice.to_dict()
    })

@api_bp.route('/invoices', methods=['POST'])
@login_required
def create_invoice():
    """Create a new invoice."""
    data = request.get_json()
    
    # Get company
    company = Company.query.filter_by(user_id=current_user.id, is_primary=True).first()
    
    invoice = InvoiceService.create_invoice(current_user, data, company)
    
    return jsonify({
        'status': 'success',
        'message': 'Invoice created',
        'data': invoice.to_dict()
    }), 201

@api_bp.route('/invoices/<int:invoice_id>', methods=['PUT'])
@login_required
def update_invoice(invoice_id):
    """Update an existing invoice."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    data = request.get_json()
    invoice = InvoiceService.update_invoice(invoice, data)
    
    return jsonify({
        'status': 'success',
        'message': 'Invoice updated',
        'data': invoice.to_dict()
    })

@api_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@login_required
def delete_invoice(invoice_id):
    """Delete an invoice."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    invoice_number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Invoice {invoice_number} deleted'
    })

@api_bp.route('/invoices/<int:invoice_id>/status', methods=['PUT'])
@login_required
def update_invoice_status(invoice_id):
    """Update invoice status."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status == 'paid':
        InvoiceService.mark_as_paid(invoice)
    elif new_status == 'cancelled':
        InvoiceService.mark_as_cancelled(invoice)
    else:
        invoice.status = new_status
        db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Invoice status updated to {new_status}',
        'data': invoice.to_dict()
    })

# ==================== Customer API ====================

@api_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Get all customers for the current user."""
    customers = Customer.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(Customer.name.asc()).all()
    
    return jsonify({
        'status': 'success',
        'data': [c.to_dict() for c in customers]
    })

@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    """Get a specific customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    return jsonify({
        'status': 'success',
        'data': customer.to_dict()
    })

@api_bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    """Create a new customer."""
    data = request.get_json()
    
    customer = Customer(
        user_id=current_user.id,
        name=data.get('name'),
        company_name=data.get('company_name'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        country=data.get('country', 'Nigeria'),
        tax_id=data.get('tax_id'),
        notes=data.get('notes')
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Customer created',
        'data': customer.to_dict()
    }), 201

@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    """Update a customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    for field in ['name', 'company_name', 'email', 'phone', 'address', 
                  'city', 'state', 'country', 'tax_id', 'notes']:
        if field in data:
            setattr(customer, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Customer updated',
        'data': customer.to_dict()
    })

@api_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    """Delete a customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    customer.is_active = False
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Customer deleted'
    })

# ==================== Company API ====================

@api_bp.route('/company', methods=['GET'])
@login_required
def get_company():
    """Get user's primary company."""
    company = Company.query.filter_by(
        user_id=current_user.id,
        is_primary=True
    ).first()
    
    if not company:
        return jsonify({
            'status': 'success',
            'data': None
        })
    
    return jsonify({
        'status': 'success',
        'data': company.to_dict()
    })

@api_bp.route('/company', methods=['PUT'])
@login_required
def update_company():
    """Update user's primary company."""
    company = Company.query.filter_by(
        user_id=current_user.id,
        is_primary=True
    ).first()
    
    if not company:
        company = Company(user_id=current_user.id, is_primary=True)
        db.session.add(company)
    
    data = request.get_json()
    
    for field in ['name', 'address', 'city', 'state', 'country', 'phone', 
                  'email', 'website', 'tax_id', 'bank_name', 'account_number', 
                  'account_name', 'payment_instructions']:
        if field in data:
            setattr(company, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Company updated',
        'data': company.to_dict()
    })

# ==================== Subscription API ====================

@api_bp.route('/subscription', methods=['GET'])
@login_required
def get_subscription():
    """Get user's subscription info."""
    subscription = SubscriptionService.get_or_create_subscription(current_user)
    
    return jsonify({
        'status': 'success',
        'data': subscription.to_dict()
    })

@api_bp.route('/subscription/check-limit', methods=['GET'])
@login_required
def check_invoice_limit():
    """Check if user can create more invoices."""
    can_create = SubscriptionService.check_invoice_limit(current_user)
    
    return jsonify({
        'status': 'success',
        'can_create_invoice': can_create
    })

# ==================== Stats API ====================

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get dashboard statistics."""
    stats = InvoiceService.get_invoice_stats(current_user.id)
    customer_count = Customer.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    return jsonify({
        'status': 'success',
        'data': {
            **stats,
            'customer_count': customer_count
        }
    })