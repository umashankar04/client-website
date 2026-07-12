"""
routes/client.py
────────────────
Client-only pages: dashboard, payment history, invoice download.
Clients can only VIEW their own data.
"""

import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user

import config
from utils.excel_manager import read_rows
from utils.helpers import safe_float
from utils import db as _db

client_bp = Blueprint("client", __name__, url_prefix="/client")

WORK_FILE     = os.path.join(config.DATA_DIR, "work_records.xlsx")
PAYMENTS_FILE = os.path.join(config.DATA_DIR, "payments.xlsx")
INVOICES_FILE = os.path.join(config.DATA_DIR, "invoices.xlsx")
SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.xlsx")
CLIENTS_FILE  = os.path.join(config.DATA_DIR, "clients.xlsx")


def get_setting(key, default=""):
    if _db.is_enabled():
        try:
            return _db.get_setting(key, default)
        except Exception:
            pass
    rows = read_rows(SETTINGS_FILE)
    for r in rows:
        if r.get("key") == key:
            return r.get("value") or default
    return default


def client_only(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "client":
            flash("Access denied.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


@client_bp.route("/dashboard")
@login_required
@client_only
def dashboard():
    """Client dashboard: shows their work history and payment summary."""
    client_id = current_user.id

    if _db.is_enabled():
        works    = [w for w in _db.get_all_work()     if w.get("client_id") == client_id]
        payments = [p for p in _db.get_all_payments() if p.get("client_id") == client_id]
    else:
        works    = [w for w in read_rows(WORK_FILE)     if w.get("client_id") == client_id]
        payments = [p for p in read_rows(PAYMENTS_FILE) if p.get("client_id") == client_id]

    total_work    = len(works)
    total_billed  = sum(safe_float(w.get("total",0)) for w in works)
    total_paid    = sum(safe_float(p.get("amount_paid",0)) for p in payments)
    balance       = max(0.0, total_billed - total_paid)

    recent_works    = sorted(works,    key=lambda x: str(x.get("date","")),         reverse=True)[:5]
    recent_payments = sorted(payments, key=lambda x: str(x.get("payment_date","")), reverse=True)[:5]

    contact_phone = get_setting("contact_phone", config.DEFAULT_PHONE)
    contact_insta = get_setting("contact_instagram", config.DEFAULT_INSTAGRAM)
    qr_exists     = os.path.exists(os.path.join(config.UPLOADS_DIR, "qr.png"))

    return render_template("client_dashboard.html",
        total_work=total_work,
        total_billed=total_billed,
        total_paid=total_paid,
        balance=balance,
        recent_works=recent_works,
        recent_payments=recent_payments,
        contact_phone=contact_phone,
        contact_insta=contact_insta,
        qr_exists=qr_exists,
    )


@client_bp.route("/invoice/<serial>")
@login_required
@client_only
def download_invoice(serial):
    """Let client download their own invoice PDF."""
    from utils.invoice_generator import generate_invoice as gen_pdf
    from utils.helpers import generate_id

    client_id = current_user.id
    
    if _db.is_enabled():
        works     = _db.get_all_work()
    else:
        works     = read_rows(WORK_FILE)
        
    work      = next((w for w in works if w.get("serial") == serial), None)

    if not work or work.get("client_id") != client_id:
        abort(403)

    if _db.is_enabled():
        invoices = _db.get_all_invoices()
        payments = [p for p in _db.get_all_payments() if p.get("client_id") == client_id]
        clients  = _db.get_all_clients()
        
        # Load DB settings
        settings_rows = read_rows(SETTINGS_FILE)
        settings = {r["key"]: _db.get_setting(r["key"], r.get("value","")) for r in settings_rows}
    else:
        invoices = read_rows(INVOICES_FILE)
        payments = [p for p in read_rows(PAYMENTS_FILE) if p.get("client_id") == client_id]
        clients  = read_rows(CLIENTS_FILE)
        
        settings_rows = read_rows(SETTINGS_FILE)
        settings = {r["key"]: r.get("value","") for r in settings_rows}

    client   = next((c for c in clients if c.get("client_id") == client_id), {})

    existing   = next((inv for inv in invoices if inv.get("serial") == serial), None)
    invoice_no = existing.get("invoice_no") if existing else generate_id("INV", invoices, "invoice_no")

    total_amt  = safe_float(work.get("total", 0))
    paid_total = sum(safe_float(p.get("amount_paid", 0)) for p in payments)
    balance    = max(0.0, total_amt - paid_total)
    last_pay   = payments[-1] if payments else {}

    pdf_filename = f"{invoice_no}.pdf"
    pdf_path     = os.path.join(config.INVOICES_DIR, pdf_filename)

    if not os.path.exists(pdf_path):
        inv_data = {
            "invoice_no":     invoice_no,
            "date":           str(work.get("date",""))[:10],
            "client_name":    client.get("name",""),
            "client_mobile":  client.get("mobile",""),
            "client_email":   client.get("email",""),
            "client_address": client.get("address",""),
            "service_name":   work.get("service_name",""),
            "quantity":       work.get("quantity", 1),
            "unit_price":     safe_float(work.get("price", 0)),
            "total":          total_amt,
            "amount_paid":    paid_total,
            "balance":        balance,
            "payment_status": "Paid" if balance <= 0.01 else ("Partial" if paid_total > 0 else "Pending"),
            "payment_method": last_pay.get("payment_method",""),
            "txn_id":         last_pay.get("txn_id",""),
            "footer_text":    settings.get("invoice_footer", config.DEFAULT_FOOTER),
            "contact_phone":  settings.get("contact_phone", config.DEFAULT_PHONE),
        }
        gen_pdf(inv_data, pdf_path)

    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
