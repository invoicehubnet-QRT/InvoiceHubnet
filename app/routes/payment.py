"""
Payment Routes
==============
Handles payment processing, callbacks, and confirmation pages.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.payment import Payment, PaymentStatus, PaymentGateway
from app.services.payment_service import PaymentService

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/callback/flutterwave')
def flutterwave_callback():
    """Handle Flutterwave payment callback."""
    tx_ref = request.args.get('tx_ref')
    transaction_id = request.args.get('transaction_id')
    status = request.args.get('status')
    
    if not tx_ref:
        flash('Invalid payment callback.', 'error')
        return redirect(url_for('subscription.manage'))
    
    # Verify and complete payment
    result = PaymentService.verify_and_complete_flutterwave_payment(transaction_id, tx_ref)
    
    if result.get('status') == 'success':
        return redirect(url_for('payment.success', gateway='flutterwave'))
    else:
        return redirect(url_for('payment.failed', gateway='flutterwave', message=result.get('message', 'Payment verification failed')))

@payment_bp.route('/callback/stripe')
def stripe_callback():
    """Handle Stripe payment callback."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid payment callback.', 'error')
        return redirect(url_for('subscription.manage'))
    
    # Verify and complete payment
    result = PaymentService.verify_and_complete_stripe_payment(session_id)
    
    if result.get('status') == 'success':
        return redirect(url_for('payment.success', gateway='stripe'))
    else:
        return redirect(url_for('payment.failed', gateway='stripe', message=result.get('message', 'Payment verification failed')))

@payment_bp.route('/success')
@login_required
def success():
    """Payment success page."""
    gateway = request.args.get('gateway', 'flutterwave')
    
    # Get latest successful payment
    payment = Payment.query.filter_by(
        user_id=current_user.id,
        status=PaymentStatus.COMPLETED.value
    ).order_by(Payment.created_at.desc()).first()
    
    return render_template('payment/success.html', payment=payment, gateway=gateway)

@payment_bp.route('/canceled')
@login_required
def canceled():
    """Payment canceled page."""
    return render_template('payment/canceled.html')

@payment_bp.route('/failed')
@login_required
def failed():
    """Payment failed page."""
    gateway = request.args.get('gateway', 'unknown')
    message = request.args.get('message', 'An error occurred during payment processing.')
    
    return render_template('payment/failed.html', gateway=gateway, message=message)

@payment_bp.route('/webhook/flutterwave', methods=['POST'])
def flutterwave_webhook():
    """Handle Flutterwave webhook."""
    payload = request.get_data(as_text=True)
    signature = request.headers.get('Verif-Hash')
    
    result = PaymentService.handle_webhook('flutterwave', payload, signature)
    
    return {'status': result.get('status', 'error')}

@payment_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook."""
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    result = PaymentService.handle_webhook('stripe', payload, signature)
    
    return {'status': result.get('status', 'error')}

@payment_bp.route('/history')
@login_required
def history():
    """Payment history page."""
    from app.models.subscription import Subscription
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    payments = Payment.query.filter_by(
        user_id=current_user.id
    ).order_by(Payment.created_at.desc()).all()
    
    return render_template('payment/history.html', payments=payments, subscription=subscription)