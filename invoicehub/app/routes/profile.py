"""
Profile Routes
==============
Handles user profile management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models.company import Company
from app.models.activity_log import ActivityLog, ActivityType

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def index():
    """User profile page."""
    return render_template('profile/index.html')

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit profile page."""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not first_name or not last_name:
            flash('First name and last name are required.', 'error')
            return redirect(url_for('profile.edit'))
        
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.phone = phone or None
        
        db.session.commit()
        
        ActivityLog.log(
            user_id=current_user.id,
            activity_type=ActivityType.PROFILE_UPDATED,
            description='Profile updated'
        )
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('profile/edit.html')

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('profile.change_password'))
        
        if not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters.', 'error')
            return redirect(url_for('profile.change_password'))
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('profile.change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        
        ActivityLog.log(
            user_id=current_user.id,
            activity_type=ActivityType.PROFILE_UPDATED,
            description='Password changed'
        )
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('profile/change_password.html')

@profile_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    """Company profile management."""
    company = Company.query.filter_by(user_id=current_user.id, is_primary=True).first()
    
    if request.method == 'POST':
        if not company:
            company = Company(user_id=current_user.id, is_primary=True)
            db.session.add(company)
        
        company.name = request.form.get('name', '').strip()
        company.address = request.form.get('address', '').strip()
        company.city = request.form.get('city', '').strip()
        company.state = request.form.get('state', '').strip()
        company.country = request.form.get('country', 'Nigeria').strip()
        company.phone = request.form.get('phone', '').strip()
        company.email = request.form.get('email', '').strip()
        company.website = request.form.get('website', '').strip()
        company.tax_id = request.form.get('tax_id', '').strip()
        company.bank_name = request.form.get('bank_name', '').strip()
        company.account_number = request.form.get('account_number', '').strip()
        company.account_name = request.form.get('account_name', '').strip()
        company.payment_instructions = request.form.get('payment_instructions', '').strip()
        
        # Handle logo upload
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = logo_file.filename.rsplit('.', 1)[1].lower() if '.' in logo_file.filename else ''
            
            if ext in allowed_extensions:
                from flask import current_app
                filename = secure_filename(f"company_{current_user.id}_logo.{ext}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                filepath = os.path.join(upload_folder, filename)
                logo_file.save(filepath)
                company.logo = f'/static/uploads/{filename}'
            else:
                flash('Invalid file type. Please upload PNG, JPG, GIF, or WebP.', 'error')
                return render_template('profile/company.html', company=company)
        
        db.session.commit()
        
        ActivityLog.log(
            user_id=current_user.id,
            activity_type=ActivityType.COMPANY_UPDATED,
            description=f'Company profile updated: {company.name}'
        )
        
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('profile.company'))
    
    return render_template('profile/company.html', company=company)