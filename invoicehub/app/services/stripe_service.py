"""
Stripe Payment Service
======================
Handles payment processing with Stripe API.
"""

import stripe
from datetime import datetime
from flask import current_app

class StripeService:
    """Service for Stripe payment integration."""
    
    @classmethod
    def get_config(cls):
        """Get Stripe configuration."""
        return {
            'public_key': current_app.config.get('STRIPE_PUBLIC_KEY'),
            'secret_key': current_app.config.get('STRIPE_SECRET_KEY'),
            'webhook_secret': current_app.config.get('STRIPE_WEBHOOK_SECRET')
        }
    
    @classmethod
    def init_app(cls):
        """Initialize Stripe with secret key."""
        stripe.api_key = cls.get_config()['secret_key']
    
    @classmethod
    def create_checkout_session(cls, amount, email, name, plan_id, success_url, cancel_url):
        """
        Create a Stripe Checkout session.
        
        Args:
            amount: Amount in kobo (smallest currency unit)
            email: Customer email
            name: Customer name
            plan_id: Subscription plan ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
        
        Returns:
            dict: Checkout session data
        """
        cls.init_app()
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'ngn',
                        'unit_amount': int(amount * 100),
                        'product_data': {
                            'name': f'InvoiceHubNet {plan_id.title()} Plan',
                            'description': f'Monthly subscription to InvoiceHubNet {plan_id.title()} plan'
                        }
                    },
                    'quantity': 1
                }],
                mode='payment',
                customer_email=email,
                metadata={
                    'plan_id': plan_id,
                    'user_email': email
                },
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            return {
                'status': 'success',
                'session_id': session.id,
                'url': session.url
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe checkout error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @classmethod
    def verify_webhook_signature(cls, payload, signature):
        """
        Verify Stripe webhook signature.
        
        Args:
            payload: Raw request payload
            signature: Stripe signature header
        
        Returns:
            dict: Event data if valid, None otherwise
        """
        cls.init_app()
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                cls.get_config()['webhook_secret']
            )
            return event
        except ValueError as e:
            current_app.logger.error(f"Stripe signature error (invalid payload): {str(e)}")
            return None
        except stripe.error.SignatureVerificationError as e:
            current_app.logger.error(f"Stripe signature error (invalid signature): {str(e)}")
            return None
    
    @classmethod
    def get_session(cls, session_id):
        """Retrieve a checkout session by ID."""
        cls.init_app()
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'status': 'success',
                'session': session
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe session retrieval error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @classmethod
    def create_refund(cls, payment_intent_id, amount=None):
        """
        Create a refund for a payment.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Amount to refund (optional, full refund if not specified)
        
        Returns:
            dict: Refund data
        """
        cls.init_app()
        
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount:
                refund_params['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            
            return {
                'status': 'success',
                'refund_id': refund.id,
                'amount': refund.amount / 100
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe refund error: {str(e)}")
            return {'status': 'error', 'message': str(e)}