"""
Subscription Service
====================
Handles subscription plan logic and management.
"""

from datetime import datetime, timedelta
from app import db
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.activity_log import ActivityLog, ActivityType

# Subscription plan definitions
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free Plan',
        'price': 0,
        'price_monthly': 0,
        'currency': 'NGN',
        'invoices_per_week': 1,
        'features': [
            'Generate only 1 invoice every week',
            'Download PDF',
            'Print invoice',
            'Basic invoice template',
            'InvoiceHubNet watermark',
            'No cloud storage',
            'No invoice history',
            'Community support'
        ],
        'limitations': [
            'InvoiceHubNet watermark on invoices',
            'No cloud storage',
            'No invoice history',
            'No customer management'
        ],
        'color': '#6B7280',
        'popular': False
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 700,
        'price_monthly': 700,
        'currency': 'NGN',
        'invoices_per_week': 2,
        'features': [
            'Generate 2 invoices every week',
            'Save invoices in the cloud',
            'Invoice history',
            'Customer management',
            'Company profile',
            'Remove watermark',
            'Email invoices',
            'Basic support'
        ],
        'limitations': [
            'Basic invoice templates only',
            'No analytics'
        ],
        'color': '#3B82F6',
        'popular': False
    },
    'prime': {
        'name': 'Prime Plan',
        'price': 4000,
        'price_monthly': 4000,
        'currency': 'NGN',
        'invoices_per_week': 4,
        'features': [
            'Generate 4 invoices every week',
            'Premium invoice templates',
            'Analytics dashboard',
            'Multiple company profiles',
            'Payment reminders',
            'Custom branding',
            'Priority support'
        ],
        'limitations': [],
        'color': '#8B5CF6',
        'popular': True
    },
    'full_suite': {
        'name': 'Full Suite',
        'price': 10000,
        'price_monthly': 10000,
        'currency': 'NGN',
        'invoices_per_week': 7,
        'features': [
            'Generate 7 invoices every week',
            'Team collaboration',
            'Staff accounts',
            'Expense tracking',
            'AI invoice assistant',
            'White-label branding',
            'API access',
            'Unlimited cloud storage',
            'Early access to new Quick Red Tech products'
        ],
        'limitations': [],
        'color': '#F59E0B',
        'popular': False
    }
}

class SubscriptionService:
    """Service for managing user subscriptions."""
    
    @staticmethod
    def get_or_create_subscription(user):
        """Get existing subscription or create free plan."""
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.FREE.value,
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()
        return subscription
    
    @staticmethod
    def upgrade_subscription(user, plan_id, gateway='flutterwave', 
                             gateway_subscription_id=None, period_start=None, period_end=None):
        """Upgrade user to a new subscription plan."""
        if plan_id not in SUBSCRIPTION_PLANS:
            raise ValueError(f"Invalid plan: {plan_id}")
        
        subscription = SubscriptionService.get_or_create_subscription(user)
        old_plan = subscription.plan
        
        subscription.plan = plan_id
        subscription.status = 'active'
        subscription.payment_gateway = gateway
        subscription.gateway_subscription_id = gateway_subscription_id
        subscription.current_period_start = period_start or datetime.utcnow()
        subscription.current_period_end = period_end or (datetime.utcnow() + timedelta(days=30))
        subscription.expires_at = period_end
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log(
            user_id=user.id,
            activity_type=ActivityType.SUBSCRIPTION_UPDATED,
            description=f'Subscription upgraded from {old_plan} to {plan_id}',
            metadata={'old_plan': old_plan, 'new_plan': plan_id}
        )
        
        return subscription
    
    @staticmethod
    def cancel_subscription(user):
        """Cancel user subscription and revert to free plan."""
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        if subscription:
            subscription.plan = SubscriptionPlan.FREE.value
            subscription.status = 'cancelled'
            subscription.auto_renew = False
            db.session.commit()
            
            ActivityLog.log(
                user_id=user.id,
                activity_type=ActivityType.SUBSCRIPTION_UPDATED,
                description='Subscription cancelled'
            )
        
        return subscription
    
    @staticmethod
    def check_invoice_limit(user):
        """Check if user can create more invoices this week."""
        subscription = SubscriptionService.get_or_create_subscription(user)
        
        if subscription.plan == SubscriptionPlan.FREE.value:
            return True  # Always allow for free users (checked separately)
        
        # Count invoices created this week
        week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        from app.models.invoice import Invoice
        invoice_count = Invoice.query.filter(
            Invoice.user_id == user.id,
            Invoice.created_at >= week_start
        ).count()
        
        return invoice_count < subscription.invoices_per_week
    
    @staticmethod
    def get_plan_details(plan_id):
        """Get details for a specific plan."""
        return SUBSCRIPTION_PLANS.get(plan_id)
    
    @staticmethod
    def format_price(price, currency='NGN'):
        """Format price with currency symbol."""
        symbols = {
            'NGN': '₦',
            'USD': '$',
            'EUR': '€',
            'GBP': '£'
        }
        symbol = symbols.get(currency, '₦')
        return f"{symbol}{price:,.0f}"