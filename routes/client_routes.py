import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_file, abort, request
from flask_login import login_required, current_user

from config import Config
import models.client as client_model
import models.work as work_model
import models.payment as payment_model
import models.settings as settings_model
import models.invoice as invoice_model
import utils.pdf_generator as pdf_gen

client_bp = Blueprint('client', __name__, url_prefix='/client')

@client_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Computes view-only statistics (number of works, paid sum, pending balances),
    displays payment details, and gets contact info for the client user.
    """
    # Enforce role safety
    if current_user.role != 'client':
        return redirect(url_for('admin.dashboard'))
        
    client_id = current_user.id
    works = work_model.get_work_by_client(client_id)
    
    total_work = len(works)
    paid_amount = 0.0
    pending_amount = 0.0
    
    # Calculate finances
    for w in works:
        try:
            total_bill = float(w.get('Total', 0.0))
        except ValueError:
            total_bill = 0.0
            
        paid = payment_model.get_total_paid_for_work(w.get('Serial Number'))
        paid_amount += paid
        pending_amount += (total_bill - paid)
        
    # Get payments list
    all_payments = payment_model.get_all_payments()
    client_payments = []
    
    # Filter payments related to client's projects
    work_serials = {w.get('Serial Number') for w in works}
    for p in all_payments:
        if p.get('Work Serial Number') in work_serials:
            client_payments.append(p)
            
    client_payments.sort(key=lambda x: x.get('Payment Date', ''), reverse=True)
    
    # Load system contact settings
    settings = settings_model.get_all_settings()
    contact_phone = settings.get('contact_number', '9668797558')
    insta_link = settings.get('instagram_link', 'https://www.instagram.com/pradhan04_')
    qr_code = settings.get('qr_code_path', '')
    
    # Sort works newest first
    works.sort(key=lambda x: x.get('Date', ''), reverse=True)
    
    return render_template(
        'client/dashboard.html',
        total_work=total_work,
        paid_amount=paid_amount,
        pending_amount=pending_amount,
        works=works[:5], # Show recent 5 on dashboard
        payments=client_payments[:5],
        contact_phone=contact_phone,
        insta_link=insta_link,
        qr_code=qr_code
    )

@client_bp.route('/work-history')
@login_required
def work_history():
    """Lists client work logs, with filter constraints."""
    if current_user.role != 'client':
        return redirect(url_for('admin.dashboard'))
        
    client_id = current_user.id
    status_filter = request.args.get('status', '')
    
    all_works = work_model.get_work_by_client(client_id)
    filtered = []
    
    for w in all_works:
        if status_filter and w.get('Status') != status_filter:
            continue
        filtered.append(w)
        
    filtered.sort(key=lambda x: x.get('Date', ''), reverse=True)
    return render_template('client/work_history.html', works=filtered, selected_status=status_filter)

@client_bp.route('/contact')
@login_required
def contact():
    """Renders support screen."""
    if current_user.role != 'client':
        return redirect(url_for('admin.dashboard'))
        
    settings = settings_model.get_all_settings()
    contact_phone = settings.get('contact_number', '9668797558')
    insta_link = settings.get('instagram_link', 'https://www.instagram.com/pradhan04_')
    
    return render_template('client/contact.html', contact_phone=contact_phone, insta_link=insta_link)

@client_bp.route('/invoices/download/<work_serial>')
@login_required
def download_invoice(work_serial):
    """
    Downloads an invoice PDF for the client.
    Enforces security: clients can only download their own invoices.
    If the PDF file does not exist, it is generated dynamically.
    """
    # Load work details
    work = work_model.get_work_by_serial(work_serial)
    if not work:
        abort(404)
        
    # Security check: client must own this record
    if current_user.role == 'client' and work.get('Client ID') != current_user.id:
        flash("Unauthorized access.", "error")
        return redirect(url_for('client.dashboard'))
        
    # Check if invoice record exists
    inv_record = invoice_model.get_invoice_by_work(work_serial)
    
    # Resolve file details
    invoice_no = inv_record.get('Invoice Number') if inv_record else invoice_model.generate_next_invoice_no()
    pdf_filename = f"{invoice_no}.pdf"
    pdf_path = os.path.join(Config.INVOICES_DIR, pdf_filename)
    
    # If the physical file is missing, re-generate it
    if not os.path.exists(pdf_path):
        client = client_model.get_client_by_id(work.get('Client ID'))
        if not client:
            abort(404)
            
        settings = settings_model.get_all_settings()
        contact_info = {
            'phone': settings.get('contact_number', '9668797558'),
            'instagram': settings.get('instagram_link', 'https://www.instagram.com/pradhan04_')
        }
        
        logo_filename = settings.get('logo_path', '')
        logo_path = os.path.join(Config.UPLOADS_DIR, logo_filename) if logo_filename else None
        
        qr_filename = settings.get('qr_code_path', '')
        qr_path = os.path.join(Config.UPLOADS_DIR, qr_filename) if qr_filename else None
        
        footer_text = settings.get('invoice_footer', 'Thank you for your business!')
        amount_paid = payment_model.get_total_paid_for_work(work_serial)
        rem_balance = float(work.get('Total', 0)) - amount_paid
        
        pmts = payment_model.get_payments_by_work(work_serial)
        pmt_method = pmts[-1].get('Payment Method') if pmts else 'N/A'
        txn_id = pmts[-1].get('Transaction ID') if pmts else 'N/A'
        
        invoice_data = {
            'invoice_no': invoice_no,
            'client_name': client.get('Name'),
            'client_mobile': client.get('Mobile Number'),
            'client_email': client.get('Email'),
            'client_address': client.get('Address'),
            'date': work.get('Date'),
            'service_name': work.get('Service Type'),
            'quantity': work.get('Quantity'),
            'price': float(work.get('Price', 0)),
            'total': float(work.get('Total', 0)),
            'payment_status': work.get('Status'),
            'amount_paid': amount_paid,
            'remaining_balance': rem_balance,
            'payment_method': pmt_method,
            'transaction_id': txn_id
        }
        
        pdf_gen.generate_invoice_pdf(
            invoice_data=invoice_data,
            output_path=pdf_path,
            logo_path=logo_path,
            qr_code_path=qr_path,
            contact_info=contact_info,
            footer_text=footer_text
        )
        
        # Save record
        invoice_model.create_invoice_record(work_serial, pdf_path)
        
    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
