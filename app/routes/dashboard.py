"""
Dashboard Routes
================
Handles the main dashboard and invoice history.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.customer import Customer
from app.models.activity_log import ActivityLog
from app.services.invoice_service import InvoiceService
from app.services.subscription_service import SubscriptionService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page."""
    # Get stats
    stats = InvoiceService.get_invoice_stats(current_user.id)
    
    # Get recent invoices
    recent_invoices = InvoiceService.get_recent_invoices(current_user.id, 5)
    
    # Get recent activity
    recent_activity = ActivityLog.query.filter_by(
        user_id=current_user.id
    ).order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # Get subscription info
    subscription = SubscriptionService.get_or_create_subscription(current_user)
    
    # Get customer count
    customer_count = Customer.query.filter_by(user_id=current_user.id).count()
    
    # Get overdue invoices
    overdue_invoices = InvoiceService.get_overdue_invoices(current_user.id)
    
    return render_template('dashboard/index.html',
                         stats=stats,
                         recent_invoices=recent_invoices,
                         recent_activity=recent_activity,
                         subscription=subscription,
                         customer_count=customer_count,
                         overdue_invoices=overdue_invoices)

@dashboard_bp.route('/history')
@login_required
def history():
    """Invoice history page with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    search_query = request.args.get('q', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Build query
    query = Invoice.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                Invoice.invoice_number.ilike(f'%{search_query}%'),
                Invoice.customer.has(Customer.name.ilike(f'%{search_query}%'))
            )
        )
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date <= to_date)
        except ValueError:
            pass
    
    # Paginate
    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    invoices = pagination.items
    total_invoices = Invoice.query.filter_by(user_id=current_user.id).count()
    
    # Stats for display
    stats = InvoiceService.get_invoice_stats(current_user.id)
    
    return render_template('dashboard/history.html',
                         invoices=invoices,
                         pagination=pagination,
                         total_invoices=total_invoices,
                         stats=stats,
                         status_filter=status_filter,
                         search_query=search_query,
                         date_from=date_from,
                         date_to=date_to)

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard (requires Prime or Full Suite)."""
    subscription = SubscriptionService.get_or_create_subscription(current_user)
    
    if subscription.plan not in ['prime', 'full_suite']:
        flash('Analytics dashboard is available for Prime and Full Suite plans only.', 'info')
        return redirect(url_for('dashboard.index'))
    
    # Get monthly data for the last 6 months
    months_data = []
    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        month_invoices = Invoice.query.filter(
            Invoice.user_id == current_user.id,
            Invoice.created_at >= month_start,
            Invoice.created_at < month_end
        ).all()
        
        paid = sum(inv.total for inv in month_invoices if inv.status == InvoiceStatus.PAID.value)
        pending = sum(inv.total for inv in month_invoices if inv.status == InvoiceStatus.PENDING.value)
        
        months_data.append({
            'month': month_start.strftime('%B %Y'),
            'invoices_count': len(month_invoices),
            'paid': paid,
            'pending': pending
        })
    
    # Top customers
    customers = Customer.query.filter_by(user_id=current_user.id).order_by(
        Customer.total_invoiced.desc()
    ).limit(10).all()
    
    # Status distribution
    status_dist = {
        'draft': Invoice.query.filter_by(user_id=current_user.id, status='draft').count(),
        'pending': Invoice.query.filter_by(user_id=current_user.id, status='pending').count(),
        'paid': Invoice.query.filter_by(user_id=current_user.id, status='paid').count(),
        'cancelled': Invoice.query.filter_by(user_id=current_user.id, status='cancelled').count()
    }
    
    return render_template('dashboard/analytics.html',
                         months_data=months_data,
                         customers=customers,
                         status_dist=status_dist)

@dashboard_bp.route('/activity')
@login_required
def activity():
    """Activity log page."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    pagination = ActivityLog.query.filter_by(
        user_id=current_user.id
    ).order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    activities = pagination.items
    
    return render_template('dashboard/activity.html',
                         activities=activities,
                         pagination=pagination)