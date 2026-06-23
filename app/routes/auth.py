"""
Authentication Routes
=====================
Handles user authentication: login, register, password reset, etc.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from app import db
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.activity_log import ActivityLog, ActivityType
from app.models.password_reset import PasswordReset
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact support.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log activity
            ActivityLog.log(
                user_id=user.id,
                activity_type=ActivityType.LOGIN,
                description='User logged in',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email:
            errors.append('Email is required.')
        elif User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_verified=False,
            verification_token=User.generate_verification_token()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        # Create free subscription
        subscription = Subscription(
            user_id=user.id,
            plan=SubscriptionPlan.FREE.value,
            status='active'
        )
        db.session.add(subscription)
        
        db.session.commit()
        
        # Send verification email
        EmailService.send_verification_email(user, user.verification_token)
        
        # Log activity
        ActivityLog.log(
            user_id=user.id,
            activity_type=ActivityType.REGISTER,
            description='New user registered',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash('Account created successfully! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    ActivityLog.log(
        user_id=current_user.id,
        activity_type=ActivityType.LOGOUT,
        description='User logged out',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = PasswordReset.generate_token(user.id, request.remote_addr)
            EmailService.send_password_reset_email(user, token.token)
        
        # Always show success message to prevent email enumeration
        flash('If an account exists with this email, you will receive password reset instructions.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset page with token."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    reset = PasswordReset.verify_token(token)
    
    if not reset:
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password:
            flash('Password is required.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        user = reset.user
        user.set_password(password)
        reset.mark_used()
        db.session.commit()
        
        ActivityLog.log(
            user_id=user.id,
            activity_type=ActivityType.PASSWORD_RESET_REQUESTED,
            description='Password reset completed',
            ip_address=request.remote_addr
        )
        
        flash('Your password has been reset. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification page."""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid verification link.', 'error')
        return redirect(url_for('auth.register'))
    
    if user.is_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email."""
    email = request.form.get('email', '').lower().strip()
    
    user = User.query.filter_by(email=email).first()
    
    if user and not user.is_verified:
        user.verification_token = User.generate_verification_token()
        db.session.commit()
        EmailService.send_verification_email(user, user.verification_token)
    
    flash('If an account exists with this email and is unverified, you will receive a new verification email.', 'success')
    return redirect(url_for('auth.login'))

# Helper function for user model
def generate_verification_token(self):
    """Generate a unique verification token."""
    import secrets
    return secrets.token_urlsafe(32)