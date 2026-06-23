"""
Flutterwave Payment Service
===========================
Handles payment processing with Flutterwave API.
"""

import json
import hashlib
import requests
from datetime import datetime
from flask import current_app

class FlutterwaveService:
    """Service for Flutterwave payment integration."""
    
    BASE_URL = 'https://api.flutterwave.com/v3'
    
    @classmethod
    def get_config(cls):
        """Get Flutterwave configuration."""
        return {
            'public_key': current_app.config.get('FLUTTERWAVE_PUBLIC_KEY'),
            'secret_key': current_app.config.get('FLUTTERWAVE_SECRET_KEY'),
            'secret_hash': current_app.config.get('FLUTTERWAVE_SECRET_HASH')
        }
    
    @classmethod
    def get_headers(cls):
        """Get headers for API requests."""
        return {
            'Authorization': f"Bearer {cls.get_config()['secret_key']}",
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def create_payment(cls, amount, email, name, plan_id, tx_ref=None):
        """
        Create a payment session with Flutterwave.
        
        Args:
            amount: Amount to charge in lowest currency unit
            email: Customer email
            name: Customer name
            plan_id: Subscription plan ID
            tx_ref: Transaction reference (optional)
        
        Returns:
            dict: Payment session data including redirect URL
        """
        if tx_ref is None:
            tx_ref = f"INVHUB_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        config = cls.get_config()
        
        payload = {
            'amount': amount,
            'currency': 'NGN',
            'redirect_url': f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/payment/callback/flutterwave",
            'customer': {
                'email': email,
                'name': name
            },
            'tx_ref': tx_ref,
            'customizations': {
                'title': 'InvoiceHubNet Subscription',
                'description': f'Subscription to {plan_id} plan',
                'logo': f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/static/images/logo.png"
            },
            'metadata': {
                'plan_id': plan_id,
                'user_email': email
            }
        }
        
        try:
            response = requests.post(
                f"{cls.BASE_URL}/payments",
                headers=cls.get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            current_app.logger.error(f"Flutterwave payment error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @classmethod
    def verify_payment(cls, transaction_id):
        """
        Verify a payment transaction.
        
        Args:
            transaction_id: Flutterwave transaction ID
        
        Returns:
            dict: Transaction verification data
        """
        try:
            response = requests.get(
                f"{cls.BASE_URL}/transactions/{transaction_id}/verify",
                headers=cls.get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            current_app.logger.error(f"Flutterwave verification error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @classmethod
    def verify_webhook_signature(cls, signature, payload):
        """
        Verify Flutterwave webhook signature.
        
        Args:
            signature: Webhook signature from header
            payload: Raw request payload
        
        Returns:
            bool: True if signature is valid
        """
        secret_hash = cls.get_config()['secret_hash']
        if not secret_hash:
            return False
        
        expected_signature = hashlib.sha512(
            (payload + secret_hash).encode('utf-8')
        ).hexdigest()
        
        return signature == expected_signature
    
    @classmethod
    def get_banks(cls, country='NG'):
        """Get list of banks for a country."""
        try:
            response = requests.get(
                f"{cls.BASE_URL}/banks/{country}",
                headers=cls.get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            current_app.logger.error(f"Flutterwave bank list error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @classmethod
    def initiate_bulk_transfer(cls, bulk_data):
        """Initiate bulk transfer (for refunds, etc.)."""
        try:
            response = requests.post(
                f"{cls.BASE_URL}/bulk-transfers",
                headers=cls.get_headers(),
                json=bulk_data,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            current_app.logger.error(f"Flutterwave bulk transfer error: {str(e)}")
            return {'status': 'error', 'message': str(e)}