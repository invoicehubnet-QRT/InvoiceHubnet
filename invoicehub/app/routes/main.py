"""
Main Routes
===========
Public pages: Landing, Features, Pricing, About, Contact, etc.
"""

from flask import Blueprint, render_template, request
from flask_login import current_user
from app.services.subscription_service import SUBSCRIPTION_PLANS

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page."""
    return render_template('main/index.html')

@main_bp.route('/features')
def features():
    """Features page."""
    return render_template('main/features.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page with subscription plans."""
    return render_template('main/pricing.html', plans=SUBSCRIPTION_PLANS)

@main_bp.route('/about')
def about():
    """About page."""
    return render_template('main/about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page."""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically send an email or save to database
        # For now, we'll just acknowledge the submission
        return render_template('main/contact.html', 
                             success=True, 
                             name=name)
    
    return render_template('main/contact.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('main/privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('main/terms.html')

@main_bp.route('/sitemap.xml')
def sitemap():
    """Sitemap for SEO."""
    from flask import Response
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://invoicehubnet.vercel.app/</loc><priority>1.0</priority></url>
  <url><loc>https://invoicehubnet.vercel.app/features</loc><priority>0.8</priority></url>
  <url><loc>https://invoicehubnet.vercel.app/pricing</loc><priority>0.9</priority></url>
  <url><loc>https://invoicehubnet.vercel.app/about</loc><priority>0.6</priority></url>
  <url><loc>https://invoicehubnet.vercel.app/contact</loc><priority>0.5</priority></url>
  <url><loc>https://invoicehubnet.vercel.app/privacy</loc><priority>0.4</priority></url>
  <url><loc>https://invoicehubnet.vercel.app/terms</loc><priority>0.4</priority></url>
</urlset>'''
    return Response(xml, mimetype='application/xml')