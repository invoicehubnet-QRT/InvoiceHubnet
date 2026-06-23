"""
Customer Routes
===============
Handles customer/client management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.customer import Customer
from app.models.activity_log import ActivityLog, ActivityType

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
@login_required
def index():
    """Customer list page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('q', '')
    
    query = Customer.query.filter_by(user_id=current_user.id, is_active=True)
    
    if search_query:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search_query}%'),
                Customer.company_name.ilike(f'%{search_query}%'),
                Customer.email.ilike(f'%{search_query}%')
            )
        )
    
    pagination = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    customers = pagination.items
    total_customers = Customer.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    return render_template('customer/index.html',
                         customers=customers,
                         pagination=pagination,
                         total_customers=total_customers,
                         search_query=search_query)

@customer_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new customer."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', '').strip() or 'Nigeria'
        tax_id = request.form.get('tax_id', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('Customer name is required.', 'error')
            return render_template('customer/create.html')
        
        customer = Customer(
            user_id=current_user.id,
            name=name,
            company_name=company_name or None,
            email=email or None,
            phone=phone or None,
            address=address or None,
            city=city or None,
            state=state or None,
            country=country,
            tax_id=tax_id or None,
            notes=notes or None
        )
        
        db.session.add(customer)
        db.session.commit()
        
        ActivityLog.log(
            user_id=current_user.id,
            activity_type=ActivityType.CUSTOMER_CREATED,
            description=f'Customer {name} created',
            metadata={'customer_id': customer.id}
        )
        
        flash(f'Customer {name} created successfully!', 'success')
        return redirect(url_for('customer.index'))
    
    return render_template('customer/create.html')

@customer_bp.route('/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit(customer_id):
    """Edit customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('customer.index'))
    
    if request.method == 'POST':
        customer.name = request.form.get('name', '').strip()
        customer.company_name = request.form.get('company_name', '').strip() or None
        customer.email = request.form.get('email', '').strip() or None
        customer.phone = request.form.get('phone', '').strip() or None
        customer.address = request.form.get('address', '').strip() or None
        customer.city = request.form.get('city', '').strip() or None
        customer.state = request.form.get('state', '').strip() or None
        customer.country = request.form.get('country', '').strip() or 'Nigeria'
        customer.tax_id = request.form.get('tax_id', '').strip() or None
        customer.notes = request.form.get('notes', '').strip() or None
        
        db.session.commit()
        
        ActivityLog.log(
            user_id=current_user.id,
            activity_type=ActivityType.CUSTOMER_UPDATED,
            description=f'Customer {customer.name} updated',
            metadata={'customer_id': customer.id}
        )
        
        flash(f'Customer {customer.name} updated successfully!', 'success')
        return redirect(url_for('customer.index'))
    
    return render_template('customer/edit.html', customer=customer)

@customer_bp.route('/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete(customer_id):
    """Delete (deactivate) customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    customer.is_active = False
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Customer {customer.name} deleted'})

@customer_bp.route('/<int:customer_id>')
@login_required
def view(customer_id):
    """View customer details."""
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('customer.index'))
    
    from app.models.invoice import Invoice
    invoices = Invoice.query.filter_by(
        customer_id=customer_id,
        user_id=current_user.id
    ).order_by(Invoice.created_at.desc()).all()
    
    return render_template('customer/view.html', customer=customer, invoices=invoices)