"""
Payment Service
===============
Unified payment service handling multiple gateways.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models.payment import Payment, PaymentStatus, PaymentGateway
from app.models.subscription import Subscription
from app.services.subscription_service import SUBSCRIPTION_PLANS, SubscriptionService
from app.services.flutterwave_service import FlutterwaveService
from app.services.stripe_service import StripeService

class PaymentService:
    """Unified payment service for handling all payment operations."""
    
    @staticmethod
    def initiate_payment(user, plan_id, gateway='flutterwave'):
        """
        Initiate a payment for subscription upgrade.
        
        Args:
            user: User object
            plan_id: Plan identifier
            gateway: Payment gateway to use
        
        Returns:
            dict: Payment initiation result with redirect URL
        """
        if plan_id not in SUBSCRIPTION_PLANS:
            return {'status': 'error', 'message': f'Invalid plan: {plan_id}'}
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        amount = plan['price']
        name = user.full_name
        email = user.email
        
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        
        if gateway == PaymentGateway.FLUTTERWAVE.value:
            return PaymentService._initiate_flutterwave_payment(
                user, plan_id, amount, name, email, base_url
            )
        elif gateway == PaymentGateway.STRIPE.value:
            return PaymentService._initiate_stripe_payment(
                user, plan_id, amount, name, email, base_url
            )
        else:
            return {'status': 'error', 'message': 'Invalid payment gateway'}
    
    @staticmethod
    def _initiate_flutterwave_payment(user, plan_id, amount, name, email, base_url):
        """Initiate Flutterwave payment."""
        tx_ref = f"INVHUB_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{user.id}"
        
        # Create payment record
        payment = Payment(
            user_id=user.id,
            gateway=PaymentGateway.FLUTTERWAVE.value,
            reference=tx_ref,
            amount=amount,
            currency='NGN',
            status=PaymentStatus.PENDING.value,
            plan=plan_id
        )
        db.session.add(payment)
        db.session.commit()
        
        # Create Flutterwave payment session
        result = FlutterwaveService.create_payment(
            amount=amount,
            email=email,
            name=name,
            plan_id=plan_id,
            tx_ref=tx_ref
        )
        
        if result.get('status') == 'success':
            payment.transaction_id = result['data'].get('id')
            db.session.commit()
            return {
                'status': 'success',
                'gateway': 'flutterwave',
                'redirect_url': result['data'].get('link'),
                'payment_id': payment.id
            }
        else:
            payment.status = PaymentStatus.FAILED.value
            payment.failure_reason = result.get('message', 'Unknown error')
            db.session.commit()
            return {'status': 'error', 'message': result.get('message', 'Payment initiation failed')}
    
    @staticmethod
    def _initiate_stripe_payment(user, plan_id, amount, name, email, base_url):
        """Initiate Stripe payment."""
        success_url = f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/payment/canceled"
        
        result = StripeService.create_checkout_session(
            amount=amount,
            email=email,
            name=name,
            plan_id=plan_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if result.get('status') == 'success':
            # Create payment record
            payment = Payment(
                user_id=user.id,
                gateway=PaymentGateway.STRIPE.value,
                reference=result['session_id'],
                amount=amount,
                currency='NGN',
                status=PaymentStatus.PENDING.value,
                plan=plan_id
            )
            db.session.add(payment)
            db.session.commit()
            
            return {
                'status': 'success',
                'gateway': 'stripe',
                'redirect_url': result['url'],
                'payment_id': payment.id
            }
        else:
            return {'status': 'error', 'message': result.get('message', 'Payment initiation failed')}
    
    @staticmethod
    def verify_and_complete_flutterwave_payment(transaction_id, tx_ref):
        """
        Verify Flutterwave payment and activate subscription.
        
        Args:
            transaction_id: Flutterwave transaction ID
            tx_ref: Transaction reference
        
        Returns:
            dict: Verification result
        """
        # Find payment record
        payment = Payment.query.filter_by(reference=tx_ref).first()
        if not payment:
            return {'status': 'error', 'message': 'Payment not found'}
        
        # Verify with Flutterwave
        result = FlutterwaveService.verify_payment(transaction_id)
        
        if result.get('status') == 'success' and result['data'].get('status') == 'successful':
            payment.status = PaymentStatus.COMPLETED.value
            payment.transaction_id = transaction_id
            payment.response_data = str(result)
            db.session.commit()
            
            # Activate subscription
            period_end = datetime.utcnow() + timedelta(days=30)
            SubscriptionService.upgrade_subscription(
                user=payment.user,
                plan_id=payment.plan,
                gateway='flutterwave',
                gateway_subscription_id=transaction_id,
                period_start=datetime.utcnow(),
                period_end=period_end
            )
            
            return {'status': 'success', 'message': 'Payment verified and subscription activated'}
        else:
            payment.status = PaymentStatus.FAILED.value
            payment.failure_reason = f"Verification failed: {result.get('message', 'Unknown')}"
            db.session.commit()
            return {'status': 'error', 'message': payment.failure_reason}
    
    @staticmethod
    def verify_and_complete_stripe_payment(session_id):
        """
        Verify Stripe payment and activate subscription.
        
        Args:
            session_id: Stripe checkout session ID
        
        Returns:
            dict: Verification result
        """
        # Find payment record
        payment = Payment.query.filter_by(reference=session_id).first()
        if not payment:
            return {'status': 'error', 'message': 'Payment not found'}
        
        # Get session details
        result = StripeService.get_session(session_id)
        
        if result.get('status') == 'success':
            session = result['session']
            
            if session.payment_status == 'paid':
                payment.status = PaymentStatus.COMPLETED.value
                payment.response_data = str(session)
                db.session.commit()
                
                # Activate subscription
                period_end = datetime.utcnow() + timedelta(days=30)
                SubscriptionService.upgrade_subscription(
                    user=payment.user,
                    plan_id=payment.plan,
                    gateway='stripe',
                    gateway_subscription_id=session.payment_intent,
                    period_start=datetime.utcnow(),
                    period_end=period_end
                )
                
                return {'status': 'success', 'message': 'Payment verified and subscription activated'}
            else:
                return {'status': 'error', 'message': 'Payment not completed'}
        else:
            return {'status': 'error', 'message': result.get('message', 'Verification failed')}
    
    @staticmethod
    def handle_webhook(gateway, payload, signature=None):
        """
        Handle payment gateway webhook.
        
        Args:
            gateway: Payment gateway name
            payload: Raw webhook payload
            signature: Webhook signature
        
        Returns:
            dict: Webhook processing result
        """
        if gateway == 'flutterwave':
            return PaymentService._handle_flutterwave_webhook(payload, signature)
        elif gateway == 'stripe':
            return PaymentService._handle_stripe_webhook(payload, signature)
        else:
            return {'status': 'error', 'message': 'Unknown gateway'}
    
    @staticmethod
    def _handle_flutterwave_webhook(payload, signature):
        """Handle Flutterwave webhook."""
        if not FlutterwaveService.verify_webhook_signature(signature, payload):
            return {'status': 'error', 'message': 'Invalid signature'}
        
        import json
        data = json.loads(payload)
        
        event = data.get('event')
        tx_data = data.get('data', {})
        tx_ref = tx_data.get('tx_ref')
        
        if event == 'charge.completed' and tx_data.get('status') == 'successful':
            return PaymentService.verify_and_complete_flutterwave_payment(
                tx_data.get('id'),
                tx_ref
            )
        
        return {'status': 'success', 'message': 'Webhook processed'}
    
    @staticmethod
    def _handle_stripe_webhook(payload, signature):
        """Handle Stripe webhook."""
        event = StripeService.verify_webhook_signature(payload, signature)
        
        if not event:
            return {'status': 'error', 'message': 'Invalid signature'}
        
        if event['type'] == 'checkout.session.completed':
            session_id = event['data']['object']['id']
            return PaymentService.verify_and_complete_stripe_payment(session_id)
        
        return {'status': 'success', 'message': 'Webhook processed'}