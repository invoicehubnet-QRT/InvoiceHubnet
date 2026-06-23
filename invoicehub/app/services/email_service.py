"""
Email Service
=============
Handles all email operations using SMTP.
"""

import os
from flask import render_template, current_app
from flask_mail import Message
from app import mail

class EmailService:
    """Service for sending emails using Flask-Mail."""
    
    @staticmethod
    def send_email(to, subject, template, **kwargs):
        """
        Send an email using a template.
        
        Args:
            to: Recipient email address
            subject: Email subject
            template: Template name (without .html extension)
            **kwargs: Template variables
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            html_body = render_template(f'emails/{template}.html', **kwargs)
            text_body = render_template(f'emails/{template}.txt', **kwargs) if os.path.exists(
                os.path.join(current_app.template_folder, 'emails', f'{template}.txt')
            ) else None
            
            msg = Message(
                subject=subject,
                recipients=[to],
                html=html_body,
                body=text_body
            )
            
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Email send error: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new users."""
        return EmailService.send_email(
            to=user.email,
            subject='Welcome to InvoiceHubNet - Create Professional Invoices in Seconds',
            template='welcome',
            user=user
        )
    
    @staticmethod
    def send_verification_email(user, token):
        """Send email verification link."""
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        verify_url = f"{base_url}/auth/verify-email/{token}"
        
        return EmailService.send_email(
            to=user.email,
            subject='Verify Your InvoiceHubNet Account',
            template='verification',
            user=user,
            verify_url=verify_url
        )
    
    @staticmethod
    def send_password_reset_email(user, token):
        """Send password reset email."""
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        reset_url = f"{base_url}/auth/reset-password/{token}"
        
        return EmailService.send_email(
            to=user.email,
            subject='Reset Your InvoiceHubNet Password',
            template='password_reset',
            user=user,
            reset_url=reset_url
        )
    
    @staticmethod
    def send_subscription_confirmation(user, subscription, payment):
        """Send subscription confirmation email."""
        return EmailService.send_email(
            to=user.email,
            subject='InvoiceHubNet Subscription Confirmed',
            template='subscription_confirmed',
            user=user,
            subscription=subscription,
            payment=payment
        )
    
    @staticmethod
    def send_invoice_email(user, invoice, recipient_email):
        """
        Send invoice as email to customer.
        
        Args:
            user: User who owns the invoice
            invoice: Invoice object
            recipient_email: Customer's email address
        
        Returns:
            bool: True if sent successfully
        """
        from app.services.pdf_service import PDFService
        from io import BytesIO
        
        # Generate PDF
        pdf_data = PDFService.generate_invoice_pdf(invoice, user)
        
        # Send email with PDF attachment
        try:
            msg = Message(
                subject=f'Invoice {invoice.invoice_number} from {user.full_name}',
                recipients=[recipient_email]
            )
            
            # Add HTML body
            msg.html = render_template(
                'emails/invoice.html',
                user=user,
                invoice=invoice
            )
            
            # Attach PDF
            msg.attach(
                filename=f'Invoice-{invoice.invoice_number}.pdf',
                content_type='application/pdf',
                data=pdf_data
            )
            
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Invoice email error: {str(e)}")
            return False