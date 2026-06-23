"""
Subscription Routes
===================
Handles subscription management and upgrades.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.subscription import Subscription
from app.services.subscription_service import SubscriptionService, SUBSCRIPTION_PLANS

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/')
@login_required
def manage():
    """Subscription management page."""
    subscription = SubscriptionService.get_or_create_subscription(current_user)
    current_plan = SUBSCRIPTION_PLANS.get(subscription.plan, SUBSCRIPTION_PLANS['free'])
    
    # Get invoice usage this week
    from datetime import timedelta
    week_start = datetime.utcnow() - timedelta(days=7)
    from app.models.invoice import Invoice
    invoices_this_week = Invoice.query.filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= week_start
    ).count()
    
    invoices_remaining = max(0, subscription.invoices_per_week - invoices_this_week)
    
    return render_template('subscription/manage.html',
                         subscription=subscription,
                         current_plan=current_plan,
                         plans=SUBSCRIPTION_PLANS,
                         invoices_this_week=invoices_this_week,
                         invoices_remaining=invoices_remaining)

@subscription_bp.route('/upgrade/<plan_id>', methods=['GET', 'POST'])
@login_required
def upgrade(plan_id):
    """Upgrade subscription plan."""
    if plan_id not in SUBSCRIPTION_PLANS:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('subscription.manage'))
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    if request.method == 'POST':
        gateway = request.form.get('gateway', 'flutterwave')
        
        # Initiate payment
        from app.services.payment_service import PaymentService
        result = PaymentService.initiate_payment(current_user, plan_id, gateway)
        
        if result.get('status') == 'success':
            return redirect(result['redirect_url'])
        else:
            flash(result.get('message', 'Payment initiation failed'), 'error')
    
    return render_template('subscription/upgrade.html',
                         plan_id=plan_id,
                         plan=plan)

@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel():
    """Cancel subscription."""
    subscription = SubscriptionService.cancel_subscription(current_user)
    
    flash('Your subscription has been cancelled. You have been moved to the Free plan.', 'info')
    return redirect(url_for('subscription.manage'))

@subscription_bp.route('/change-gateway', methods=['POST'])
@login_required
def change_gateway():
    """Change default payment gateway."""
    gateway = request.form.get('gateway', 'flutterwave')
    
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    if subscription:
        subscription.payment_gateway = gateway
        db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Default gateway changed to {gateway}'})