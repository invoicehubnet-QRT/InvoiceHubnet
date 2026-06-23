"""
PDF Service
===========
Handles PDF generation using ReportLab.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

class PDFService:
    """Service for generating professional PDF invoices."""
    
    @staticmethod
    def generate_invoice_pdf(invoice, user):
        """
        Generate a PDF invoice.
        
        Args:
            invoice: Invoice object
            user: User object (invoice owner)
        
        Returns:
            bytes: PDF content
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2563EB')
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#1F2937')
        )
        normal_style = styles['Normal']
        
        # Build document content
        story = []
        
        # Header with InvoiceHubNet branding
        header_data = [
            [Paragraph('<font color="#2563EB"><b>INVOICE</b></font>', 
                      ParagraphStyle('Title', fontSize=28, alignment=TA_LEFT)),
             Paragraph(f'#{invoice.invoice_number}', 
                      ParagraphStyle('InvoiceNum', fontSize=18, alignment=TA_RIGHT, 
                                   textColor=colors.HexColor('#6B7280')))]
        ]
        header_table = Table(header_data, colWidths=[10*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Divider
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#E5E7EB')))
        story.append(Spacer(1, 0.5*cm))
        
        # Company and Customer info
        company = invoice.company
        
        # Left column - Company info
        company_info = []
        if company:
            if company.name:
                company_info.append(Paragraph(f'<b>{company.name}</b>', normal_style))
            if company.address:
                company_info.append(Paragraph(company.address, normal_style))
            if company.city or company.state:
                location = ', '.join(filter(None, [company.city, company.state]))
                if location:
                    company_info.append(Paragraph(location, normal_style))
            if company.country:
                company_info.append(Paragraph(company.country, normal_style))
            if company.phone:
                company_info.append(Paragraph(f'Phone: {company.phone}', normal_style))
            if company.email:
                company_info.append(Paragraph(f'Email: {company.email}', normal_style))
        
        # Right column - Invoice details
        invoice_date_str = invoice.invoice_date.strftime('%B %d, %Y') if invoice.invoice_date else ''
        due_date_str = invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else ''
        
        invoice_info = [
            [Paragraph('<b>Invoice Date:</b>', normal_style), 
             Paragraph(invoice_date_str, normal_style)],
            [Paragraph('<b>Due Date:</b>', normal_style), 
             Paragraph(due_date_str, normal_style)],
            [Paragraph('<b>Status:</b>', normal_style), 
             Paragraph(f'<font color="{"#10B981" if invoice.status == "paid" else "#F59E0B"}">{invoice.status.upper()}</font>', normal_style)]
        ]
        
        info_table_data = [
            [Paragraph('<b>From:</b>', normal_style), Paragraph('<b>Bill To:</b>', normal_style)],
            [Paragraph('\n'.join(str(p) for p in company_info) if company_info else user.full_name, normal_style),
             Paragraph(f'<b>{invoice.customer.name if invoice.customer else "N/A"}</b><br/>' +
                      (f'{invoice.customer.company_name or ""}<br/>' if invoice.customer and invoice.customer.company_name else '') +
                      (f'{invoice.customer.address or ""}<br/>' if invoice.customer and invoice.customer.address else '') +
                      (f'{invoice.customer.email or ""}', normal_style))]
        ]
        
        # Two-column layout for addresses
        left_content = '<br/>'.join(str(p.text) if hasattr(p, 'text') else '' for p in company_info)
        right_content = f'<b>{invoice.customer.name if invoice.customer else "N/A"}</b><br/>'
        if invoice.customer:
            if invoice.customer.company_name:
                right_content += f'{invoice.customer.company_name}<br/>'
            if invoice.customer.address:
                right_content += f'{invoice.customer.address}<br/>'
            if invoice.customer.email:
                right_content += f'{invoice.customer.email}<br/>'
        
        address_table = Table(
            [[Paragraph('<b>From:</b>', normal_style), Paragraph('<b>Bill To:</b>', normal_style)],
             [Paragraph(left_content or user.full_name, normal_style), 
              Paragraph(right_content, normal_style)]],
            colWidths=[9*cm, 9*cm]
        )
        address_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(address_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Invoice details
        details_data = [
            ['Invoice Date:', invoice_date_str, '', 'Due Date:', due_date_str],
            ['Status:', invoice.status.upper(), '', '', '']
        ]
        details_table = Table(details_data, colWidths=[4*cm, 5*cm, 2*cm, 4*cm, 3*cm])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (4, 0), (4, -1), colors.HexColor('#6B7280')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Items table
        items_header = ['Description', 'Qty', 'Unit Price', 'Total']
        items_data = [items_header]
        
        currency_symbol = PDFService._get_currency_symbol(invoice.currency)
        
        for item in invoice.items:
            items_data.append([
                Paragraph(f'<b>{item.name}</b><br/><font size="8" color="#6B7280">{item.description or ""}</font>', normal_style),
                str(item.quantity),
                f'{currency_symbol}{item.unit_price:,.2f}',
                f'{currency_symbol}{item.total:,.2f}'
            ])
        
        items_table = Table(items_data, colWidths=[7*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            # Borders
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            # Header alignment
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Totals section
        totals_data = [
            ['', '', 'Subtotal:', f'{currency_symbol}{invoice.subtotal:,.2f}'],
        ]
        
        if invoice.discount_amount > 0:
            totals_data.append(['', '', f'Discount ({invoice.discount_percent}%):', 
                               f'-{currency_symbol}{invoice.discount_amount:,.2f}'])
        
        if invoice.tax_amount > 0:
            totals_data.append(['', '', f'Tax ({invoice.tax_percent}%):', 
                               f'{currency_symbol}{invoice.tax_amount:,.2f}'])
        
        if invoice.shipping_amount > 0:
            totals_data.append(['', '', 'Shipping:', 
                               f'{currency_symbol}{invoice.shipping_amount:,.2f}'])
        
        totals_data.append(['', '', 'Total:', f'{currency_symbol}{invoice.total:,.2f}'])
        
        totals_table = Table(totals_data, colWidths=[10*cm, 0, 4*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (2, -1), (3, -1), 12),
            ('BACKGROUND', (2, -1), (3, -1), colors.HexColor('#F3F4F6')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Payment information
        if company and (company.bank_name or company.account_number):
            story.append(Paragraph('<b>Payment Information</b>', heading_style))
            payment_info = []
            if company.bank_name:
                payment_info.append(f'Bank: {company.bank_name}')
            if company.account_number:
                payment_info.append(f'Account Number: {company.account_number}')
            if company.account_name:
                payment_info.append(f'Account Name: {company.account_name}')
            
            story.append(Paragraph('<br/>'.join(payment_info), normal_style))
            story.append(Spacer(1, 0.3*cm))
        
        # Notes and Terms
        if invoice.notes:
            story.append(Paragraph('<b>Notes</b>', heading_style))
            story.append(Paragraph(invoice.notes, normal_style))
            story.append(Spacer(1, 0.3*cm))
        
        if invoice.terms:
            story.append(Paragraph('<b>Terms & Conditions</b>', heading_style))
            story.append(Paragraph(invoice.terms, normal_style))
        
        # Footer
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
        story.append(Spacer(1, 0.3*cm))
        footer_text = Paragraph(
            'Generated by <font color="#2563EB"><b>InvoiceHubNet</b></font> - Create Professional Invoices in Seconds<br/>'
            '<font size="8" color="#9CA3AF">Built by Quick Red Tech Software Development Studio</font>',
            ParagraphStyle('Footer', fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#6B7280'))
        )
        story.append(footer_text)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def _get_currency_symbol(currency):
        """Get currency symbol for currency code."""
        symbols = {
            'NGN': '₦',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'KES': 'KSh',
            'ZAR': 'R',
            'GHS': '₵'
        }
        return symbols.get(currency, '₦')