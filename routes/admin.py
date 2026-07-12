"""
routes/admin.py
───────────────
All admin-only pages: dashboard, clients, services, work entries, settings.
"""

import os
from datetime import datetime, date
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, send_file, jsonify)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

import config
from utils.excel_manager import read_rows, write_rows, append_row, ensure_file
from utils.helpers import today_str, safe_float, safe_int, generate_id
from utils import db as _db

admin = Blueprint("admin", __name__, url_prefix="/admin")

# ── File paths ────────────────────────────────────────────────────────────────
CLIENTS_FILE  = os.path.join(config.DATA_DIR, "clients.xlsx")
SERVICES_FILE = os.path.join(config.DATA_DIR, "services.xlsx")
WORK_FILE     = os.path.join(config.DATA_DIR, "work_records.xlsx")
PAYMENTS_FILE = os.path.join(config.DATA_DIR, "payments.xlsx")
SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.xlsx")
INVOICES_FILE = os.path.join(config.DATA_DIR, "invoices.xlsx")

CLIENT_HEADERS  = ["client_id","name","mobile","email","address","username","password","status","reg_date"]
SERVICE_HEADERS = ["service_id","name","price"]
WORK_HEADERS    = ["serial","date","client_id","client_name","service_id","service_name","quantity","price","total","notes","status"]
PAYMENT_HEADERS = ["payment_id","client_id","client_name","invoice_no","total_amount","amount_paid","balance","payment_date","payment_method","txn_id","status"]
SETTINGS_HEADERS= ["key","value"]
INVOICE_HEADERS = ["invoice_no","serial","client_id","client_name","date","total","status","pdf_path"]


def admin_only(f):
    """Decorator: redirect to login if user is not admin."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def get_setting(key, default=""):
    rows = read_rows(SETTINGS_FILE)
    for r in rows:
        if r.get("key") == key:
            return r.get("value") or default
    return default


def get_all_settings():
    rows = read_rows(SETTINGS_FILE)
    return {r["key"]: r.get("value", "") for r in rows}


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/dashboard")
@login_required
@admin_only
def dashboard():
    clients  = read_rows(CLIENTS_FILE)
    works    = read_rows(WORK_FILE)
    payments = read_rows(PAYMENTS_FILE)

    today    = today_str()
    month    = today[:7]   # YYYY-MM
    year     = today[:4]   # YYYY

    total_clients   = len(clients)
    total_projects  = len(works)
    today_work      = [w for w in works if str(w.get("date",""))[:10] == today]

    # Income calculations based on payments
    paid_today   = sum(safe_float(p.get("amount_paid")) for p in payments if str(p.get("payment_date",""))[:10] == today)
    paid_month   = sum(safe_float(p.get("amount_paid")) for p in payments if str(p.get("payment_date",""))[:7]  == month)
    paid_year    = sum(safe_float(p.get("amount_paid")) for p in payments if str(p.get("payment_date",""))[:4]  == year)
    total_paid   = sum(safe_float(p.get("amount_paid")) for p in payments)
    total_pending= sum(safe_float(p.get("balance"))     for p in payments if str(p.get("status","")).lower() != "paid")

    # Recent activities = last 8 work entries
    recent = sorted(works, key=lambda x: str(x.get("date","")), reverse=True)[:8]

    # Chart data: monthly earnings for current year
    monthly_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_values = [0.0] * 12
    for p in payments:
        pd = str(p.get("payment_date",""))
        if pd[:4] == year:
            try:
                m = int(pd[5:7]) - 1
                monthly_values[m] += safe_float(p.get("amount_paid"))
            except:
                pass

    # Pending vs Paid counts
    pending_count = sum(1 for p in payments if str(p.get("status","")).lower() in ["pending","partial"])
    paid_count    = sum(1 for p in payments if str(p.get("status","")).lower() == "paid")

    # Service usage
    svc_usage = {}
    for w in works:
        sn = str(w.get("service_name","Unknown"))
        svc_usage[sn] = svc_usage.get(sn, 0) + 1
    top_services = sorted(svc_usage.items(), key=lambda x: x[1], reverse=True)[:5]

    settings = get_all_settings()
    contact_phone = settings.get("contact_phone", config.DEFAULT_PHONE)
    contact_insta = settings.get("contact_instagram", config.DEFAULT_INSTAGRAM)

    return render_template("admin_dashboard.html",
        total_clients=total_clients,
        total_projects=total_projects,
        today_work=len(today_work),
        total_paid=total_paid,
        total_pending=total_pending,
        paid_today=paid_today,
        paid_month=paid_month,
        paid_year=paid_year,
        recent=recent,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        pending_count=pending_count,
        paid_count=paid_count,
        top_services=top_services,
        contact_phone=contact_phone,
        contact_insta=contact_insta,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/clients")
@login_required
@admin_only
def clients():
    search = request.args.get("q","").strip().lower()
    if _db.is_enabled():
        all_clients = _db.get_all_clients()
    else:
        all_clients = read_rows(CLIENTS_FILE)
        
    if search:
        all_clients = [c for c in all_clients if
            search in str(c.get("name","")).lower() or
            search in str(c.get("username","")).lower() or
            search in str(c.get("mobile","")).lower() or
            search in str(c.get("email","")).lower()]
    return render_template("clients.html", clients=all_clients, search=search)


@admin.route("/clients/add", methods=["POST"])
@login_required
@admin_only
def add_client():
    if _db.is_enabled():
        rows = _db.get_all_clients()
    else:
        rows = read_rows(CLIENTS_FILE)
        
    client_id = generate_id("C", rows, "client_id")
    new = {
        "client_id":  client_id,
        "name":       request.form.get("name","").strip(),
        "mobile":     request.form.get("mobile","").strip(),
        "email":      request.form.get("email","").strip(),
        "address":    request.form.get("address","").strip(),
        "username":   request.form.get("username","").strip(),
        "password":   generate_password_hash(request.form.get("password","changeme")),
        "status":     "Active",
        "reg_date":   today_str(),
    }
    # Check duplicate username
    for c in rows:
        if c.get("username","").lower() == new["username"].lower():
            flash("Username already exists!", "danger")
            return redirect(url_for("admin.clients"))
            
    if _db.is_enabled():
        _db.create_client(new)
        
    # Always write to Excel to keep local copy in sync
    excel_rows = read_rows(CLIENTS_FILE)
    excel_rows.append(new)
    write_rows(CLIENTS_FILE, excel_rows, CLIENT_HEADERS)
    
    flash(f"Client '{new['name']}' added (ID: {client_id}).", "success")
    return redirect(url_for("admin.clients"))


@admin.route("/clients/edit", methods=["POST"])
@login_required
@admin_only
def edit_client():
    client_id = request.form.get("client_id")
    name = request.form.get("name","").strip()
    mobile = request.form.get("mobile","").strip()
    email = request.form.get("email","").strip()
    address = request.form.get("address","").strip()
    status = request.form.get("status","Active")

    if _db.is_enabled():
        update_data = {}
        if name: update_data["name"] = name
        if mobile: update_data["mobile"] = mobile
        if email: update_data["email"] = email
        if address: update_data["address"] = address
        if status: update_data["status"] = status
        _db.update_client(client_id, update_data)

    rows = read_rows(CLIENTS_FILE)
    for c in rows:
        if c.get("client_id") == client_id:
            c["name"]    = name or c["name"]
            c["mobile"]  = mobile or c["mobile"]
            c["email"]   = email or c["email"]
            c["address"] = address or c["address"]
            c["status"]  = status or c["status"]
            break
    write_rows(CLIENTS_FILE, rows, CLIENT_HEADERS)
    flash("Client updated.", "success")
    return redirect(url_for("admin.clients"))


@admin.route("/clients/delete/<client_id>", methods=["POST"])
@login_required
@admin_only
def delete_client(client_id):
    if _db.is_enabled():
        _db.delete_client(client_id)

    rows = read_rows(CLIENTS_FILE)
    rows = [c for c in rows if c.get("client_id") != client_id]
    write_rows(CLIENTS_FILE, rows, CLIENT_HEADERS)
    flash("Client deleted.", "success")
    return redirect(url_for("admin.clients"))


@admin.route("/clients/toggle/<client_id>", methods=["POST"])
@login_required
@admin_only
def toggle_client(client_id):
    new_status = "Active"
    rows = read_rows(CLIENTS_FILE)
    for c in rows:
        if c.get("client_id") == client_id:
            c["status"] = "Inactive" if c.get("status") == "Active" else "Active"
            new_status = c["status"]
            break
    write_rows(CLIENTS_FILE, rows, CLIENT_HEADERS)

    if _db.is_enabled():
        _db.update_client(client_id, {"status": new_status})

    flash("Client status toggled.", "success")
    return redirect(url_for("admin.clients"))


@admin.route("/clients/reset-password", methods=["POST"])
@login_required
@admin_only
def reset_client_password():
    client_id = request.form.get("client_id")
    new_pw    = request.form.get("new_password","changeme123")
    hashed_pw = generate_password_hash(new_pw)

    if _db.is_enabled():
        _db.update_client_password(client_id, hashed_pw)

    rows = read_rows(CLIENTS_FILE)
    for c in rows:
        if c.get("client_id") == client_id:
            c["password"] = hashed_pw
            break
    write_rows(CLIENTS_FILE, rows, CLIENT_HEADERS)
    flash("Password reset successfully.", "success")
    return redirect(url_for("admin.clients"))


# ══════════════════════════════════════════════════════════════════════════════
# SERVICES
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/services")
@login_required
@admin_only
def services():
    svcs = read_rows(SERVICES_FILE)
    return render_template("services.html", services=svcs)


@admin.route("/services/add", methods=["POST"])
@login_required
@admin_only
def add_service():
    rows = read_rows(SERVICES_FILE)
    svc_id = generate_id("S", rows, "service_id")
    new = {
        "service_id": svc_id,
        "name":       request.form.get("name","").strip(),
        "price":      safe_float(request.form.get("price", 0)),
    }
    rows.append(new)
    write_rows(SERVICES_FILE, rows, SERVICE_HEADERS)
    flash("Service added.", "success")
    return redirect(url_for("admin.services"))


@admin.route("/services/edit", methods=["POST"])
@login_required
@admin_only
def edit_service():
    svc_id = request.form.get("service_id")
    rows = read_rows(SERVICES_FILE)
    for s in rows:
        if s.get("service_id") == svc_id:
            s["name"]  = request.form.get("name", s["name"])
            s["price"] = safe_float(request.form.get("price", s["price"]))
            break
    write_rows(SERVICES_FILE, rows, SERVICE_HEADERS)
    flash("Service updated.", "success")
    return redirect(url_for("admin.services"))


@admin.route("/services/delete/<svc_id>", methods=["POST"])
@login_required
@admin_only
def delete_service(svc_id):
    rows = read_rows(SERVICES_FILE)
    rows = [s for s in rows if s.get("service_id") != svc_id]
    write_rows(SERVICES_FILE, rows, SERVICE_HEADERS)
    flash("Service deleted.", "success")
    return redirect(url_for("admin.services"))


# ══════════════════════════════════════════════════════════════════════════════
# WORK ENTRIES
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/work")
@login_required
@admin_only
def work():
    # Filters
    search  = request.args.get("q","").strip().lower()
    f_status= request.args.get("status","")
    f_date  = request.args.get("date_filter","")

    works   = read_rows(WORK_FILE)
    clients = read_rows(CLIENTS_FILE)
    services= read_rows(SERVICES_FILE)

    today   = today_str()
    month   = today[:7]
    year    = today[:4]

    def passes_date(w):
        d = str(w.get("date",""))[:10]
        if f_date == "today":   return d == today
        if f_date == "month":   return d[:7] == month
        if f_date == "year":    return d[:4] == year
        return True

    filtered = []
    for w in works:
        if search and search not in str(w.get("client_name","")).lower():
            continue
        if f_status and w.get("status","") != f_status:
            continue
        if not passes_date(w):
            continue
        filtered.append(w)

    filtered.sort(key=lambda x: str(x.get("date","")), reverse=True)

    return render_template("work.html",
        works=filtered, clients=clients, services=services,
        search=search, f_status=f_status, f_date=f_date,
        today=today)


@admin.route("/work/add", methods=["POST"])
@login_required
@admin_only
def add_work():
    works   = read_rows(WORK_FILE)
    clients = read_rows(CLIENTS_FILE)
    services= read_rows(SERVICES_FILE)

    serial     = generate_id("W", works, "serial")
    client_id  = request.form.get("client_id","")
    service_id = request.form.get("service_id","")
    quantity   = safe_int(request.form.get("quantity", 1))
    price      = safe_float(request.form.get("price", 0))
    total      = quantity * price

    # Lookup names
    client_name  = next((c["name"] for c in clients  if c.get("client_id")  == client_id),  "")
    service_name = next((s["name"] for s in services if s.get("service_id") == service_id), "")

    new = {
        "serial":       serial,
        "date":         request.form.get("date", today_str()),
        "client_id":    client_id,
        "client_name":  client_name,
        "service_id":   service_id,
        "service_name": service_name,
        "quantity":     quantity,
        "price":        price,
        "total":        total,
        "notes":        request.form.get("notes",""),
        "status":       request.form.get("status","Pending"),
    }
    works.append(new)
    write_rows(WORK_FILE, works, WORK_HEADERS)
    flash(f"Work entry {serial} added (Total: ₹{total:.2f}).", "success")
    return redirect(url_for("admin.work"))


@admin.route("/work/delete/<serial>", methods=["POST"])
@login_required
@admin_only
def delete_work(serial):
    works = read_rows(WORK_FILE)
    works = [w for w in works if w.get("serial") != serial]
    write_rows(WORK_FILE, works, WORK_HEADERS)
    flash("Work entry deleted.", "success")
    return redirect(url_for("admin.work"))


@admin.route("/work/toggle-status/<serial>", methods=["POST"])
@login_required
@admin_only
def toggle_work_status(serial):
    """Update status of a work entry (reflected to the client dashboard)."""
    status = request.form.get("status")
    if status not in ["Pending", "Completed", "Cancelled"]:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.work"))

    works = read_rows(WORK_FILE)
    updated = False
    for w in works:
        if w.get("serial") == serial:
            w["status"] = status
            updated = True
            break
    if updated:
        write_rows(WORK_FILE, works, WORK_HEADERS)
        flash(f"Work entry {serial} status updated to {status}.", "success")
    else:
        flash("Work entry not found.", "danger")
    return redirect(url_for("admin.work"))


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/payments")
@login_required
@admin_only
def payments():
    search   = request.args.get("q","").strip().lower()
    f_status = request.args.get("status","")
    all_pmts = read_rows(PAYMENTS_FILE)
    clients  = read_rows(CLIENTS_FILE)

    filtered = []
    for p in all_pmts:
        if search and search not in str(p.get("client_name","")).lower() and search not in str(p.get("invoice_no","")).lower():
            continue
        if f_status and str(p.get("status","")).lower() != f_status.lower():
            continue
        filtered.append(p)

    filtered.sort(key=lambda x: str(x.get("payment_date","")), reverse=True)
    return render_template("payments.html",
        payments=filtered, clients=clients,
        search=search, f_status=f_status)


@admin.route("/payments/add", methods=["POST"])
@login_required
@admin_only
def add_payment():
    payments = read_rows(PAYMENTS_FILE)
    clients  = read_rows(CLIENTS_FILE)
    invoices = read_rows(INVOICES_FILE)

    pay_id     = generate_id("P", payments, "payment_id")
    client_id  = request.form.get("client_id","")
    client_name= next((c["name"] for c in clients if c.get("client_id")==client_id),"")
    invoice_no = request.form.get("invoice_no","")
    total_amt  = safe_float(request.form.get("total_amount",0))
    amount_paid= safe_float(request.form.get("amount_paid",0))
    balance    = max(0.0, total_amt - amount_paid)

    # Determine status
    if balance <= 0.01:
        status = "Paid"
    elif amount_paid > 0:
        status = "Partial"
    else:
        status = "Pending"

    new = {
        "payment_id":    pay_id,
        "client_id":     client_id,
        "client_name":   client_name,
        "invoice_no":    invoice_no,
        "total_amount":  total_amt,
        "amount_paid":   amount_paid,
        "balance":       balance,
        "payment_date":  request.form.get("payment_date", today_str()),
        "payment_method":request.form.get("payment_method","UPI"),
        "txn_id":        request.form.get("txn_id",""),
        "status":        status,
    }
    payments.append(new)
    write_rows(PAYMENTS_FILE, payments, PAYMENT_HEADERS)
    flash(f"Payment {pay_id} recorded (Status: {status}).", "success")
    return redirect(url_for("admin.payments"))


@admin.route("/payments/delete/<pay_id>", methods=["POST"])
@login_required
@admin_only
def delete_payment(pay_id):
    payments = read_rows(PAYMENTS_FILE)
    payments = [p for p in payments if p.get("payment_id") != pay_id]
    write_rows(PAYMENTS_FILE, payments, PAYMENT_HEADERS)
    flash("Payment deleted.", "success")
    return redirect(url_for("admin.payments"))


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE GENERATION
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/invoice/generate/<serial>")
@login_required
@admin_only
def generate_invoice(serial):
    from utils.invoice_generator import generate_invoice as gen_pdf

    works    = read_rows(WORK_FILE)
    payments = read_rows(PAYMENTS_FILE)
    invoices = read_rows(INVOICES_FILE)
    clients  = read_rows(CLIENTS_FILE)
    settings = get_all_settings()

    # Find work entry
    work = next((w for w in works if w.get("serial") == serial), None)
    if not work:
        flash("Work entry not found.", "danger")
        return redirect(url_for("admin.work"))

    client = next((c for c in clients if c.get("client_id") == work.get("client_id")), {})

    # Calculate paid & balance
    total_amt  = safe_float(work.get("total", 0))
    paid_total = sum(safe_float(p.get("amount_paid",0)) for p in payments
                     if p.get("client_id") == work.get("client_id"))
    balance    = max(0.0, total_amt - paid_total)

    # Get or create invoice number
    existing = next((inv for inv in invoices if inv.get("serial") == serial), None)
    if existing:
        invoice_no = existing.get("invoice_no")
    else:
        invoice_no = generate_id("INV", invoices, "invoice_no")

    # Latest payment info
    client_payments = [p for p in payments if p.get("client_id") == work.get("client_id")]
    last_pay = client_payments[-1] if client_payments else {}

    pdf_filename = f"{invoice_no}.pdf"
    pdf_path     = os.path.join(config.INVOICES_DIR, pdf_filename)

    inv_data = {
        "invoice_no":     invoice_no,
        "date":           str(work.get("date",""))[:10],
        "client_name":    client.get("name",""),
        "client_mobile":  client.get("mobile",""),
        "client_email":   client.get("email",""),
        "client_address": client.get("address",""),
        "service_name":   work.get("service_name",""),
        "quantity":       work.get("quantity", 1),
        "unit_price":     safe_float(work.get("price",0)),
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

    # Save invoice record
    if not existing:
        invoices.append({
            "invoice_no": invoice_no,
            "serial":     serial,
            "client_id":  work.get("client_id",""),
            "client_name":client.get("name",""),
            "date":       today_str(),
            "total":      total_amt,
            "status":     inv_data["payment_status"],
            "pdf_path":   pdf_path,
        })
        write_rows(INVOICES_FILE, invoices, INVOICE_HEADERS)

    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)


# ══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/reports")
@login_required
@admin_only
def reports():
    works    = read_rows(WORK_FILE)
    payments = read_rows(PAYMENTS_FILE)
    clients  = read_rows(CLIENTS_FILE)
    services = read_rows(SERVICES_FILE)

    report_type = request.args.get("type","monthly")
    today = today_str()
    month = today[:7]
    year  = today[:4]

    def filter_works(ws):
        if report_type == "daily":   return [w for w in ws if str(w.get("date",""))[:10] == today]
        if report_type == "weekly":
            from datetime import timedelta
            week_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
            return [w for w in ws if str(w.get("date",""))[:10] >= week_ago]
        if report_type == "monthly": return [w for w in ws if str(w.get("date",""))[:7] == month]
        if report_type == "yearly":  return [w for w in ws if str(w.get("date",""))[:4] == year]
        client_filter = request.args.get("client_id","")
        if report_type == "client" and client_filter:
            return [w for w in ws if w.get("client_id") == client_filter]
        service_filter = request.args.get("service_id","")
        if report_type == "service" and service_filter:
            return [w for w in ws if w.get("service_id") == service_filter]
        return ws

    filtered = filter_works(works)
    total_amount  = sum(safe_float(w.get("total",0)) for w in filtered)
    total_entries = len(filtered)

    return render_template("reports.html",
        works=filtered,
        total_amount=total_amount,
        total_entries=total_entries,
        report_type=report_type,
        clients=clients,
        services=services,
    )


@admin.route("/reports/export-excel")
@login_required
@admin_only
def export_excel():
    """Export current report as Excel download."""
    import io
    from openpyxl import Workbook as OWB

    works = read_rows(WORK_FILE)
    wb = OWB()
    ws = wb.active
    ws.title = "Work Report"
    ws.append(["Serial","Date","Client","Service","Qty","Price","Total","Status","Notes"])
    for w in works:
        ws.append([w.get("serial"),str(w.get("date",""))[:10],w.get("client_name"),
                   w.get("service_name"),w.get("quantity"),w.get("price"),
                   w.get("total"),w.get("status"),w.get("notes")])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name="vems_report.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/settings", methods=["GET","POST"])
@login_required
@admin_only
def settings():
    from utils.backup import create_backup, list_backups, restore_backup

    if request.method == "POST":
        action = request.form.get("action","save_settings")

        if action == "save_settings":
            rows = read_rows(SETTINGS_FILE)
            settings_dict = {r["key"]: r for r in rows}

            updates = {
                "contact_phone":    request.form.get("contact_phone", config.DEFAULT_PHONE),
                "contact_instagram":request.form.get("contact_instagram", config.DEFAULT_INSTAGRAM),
                "invoice_footer":   request.form.get("invoice_footer", config.DEFAULT_FOOTER),
                # Admin login email
                "admin_email":      request.form.get("admin_email", "").strip().lower(),
                # SMTP configuration
                "smtp_host":        request.form.get("smtp_host",     "smtp.gmail.com"),
                "smtp_port":        request.form.get("smtp_port",     "587"),
                "smtp_email":       request.form.get("smtp_email",    "").strip(),
                "smtp_password":    request.form.get("smtp_password", ""),
                "smtp_name":        request.form.get("smtp_name",     "VEMS"),
            }
            for k, v in updates.items():
                if k in settings_dict:
                    settings_dict[k]["value"] = v
                else:
                    settings_dict[k] = {"key": k, "value": v}

            # Handle logo upload
            logo_file = request.files.get("logo_file")
            if logo_file and logo_file.filename:
                logo_path = os.path.join(config.UPLOADS_DIR, "logo.png")
                logo_file.save(logo_path)
                flash("Logo uploaded.", "success")

            # Handle QR upload
            qr_file = request.files.get("qr_file")
            if qr_file and qr_file.filename:
                qr_path = os.path.join(config.UPLOADS_DIR, "qr.png")
                qr_file.save(qr_path)
                flash("QR code uploaded.", "success")

            write_rows(SETTINGS_FILE, list(settings_dict.values()), ["key","value"])
            flash("Settings saved.", "success")

        elif action == "create_backup":
            fname = create_backup()
            flash(f"Backup created: {fname}", "success")

        elif action == "restore_backup":
            fname = request.form.get("backup_filename","")
            try:
                restore_backup(fname)
                flash(f"Restored from {fname}.", "success")
            except Exception as e:
                flash(str(e), "danger")

        return redirect(url_for("admin.settings"))

    all_settings = get_all_settings()
    backups      = list_backups()
    has_logo = os.path.exists(os.path.join(config.UPLOADS_DIR, "logo.png"))
    has_qr   = os.path.exists(os.path.join(config.UPLOADS_DIR, "qr.png"))

    return render_template("settings.html",
        settings=all_settings,
        backups=backups,
        has_logo=has_logo,
        has_qr=has_qr,
    )


# ══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS for Chart.js
# ══════════════════════════════════════════════════════════════════════════════
@admin.route("/api/service-price/<service_id>")
@login_required
def api_service_price(service_id):
    """Return price of a service as JSON (used by work form JS)."""
    services = read_rows(SERVICES_FILE)
    for s in services:
        if s.get("service_id") == service_id:
            return jsonify({"price": safe_float(s.get("price",0))})
    return jsonify({"price": 0})
