"""
main.py
───────
Start the Video Editing Management System with:   python main.py

This file:
  1. Creates all required folders and Excel files
  2. Sets up Flask and Flask-Login
  3. Registers all route blueprints
  4. Starts the web server
"""

import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash

import config
from utils.excel_manager import ensure_file, read_rows, write_rows

# ══════════════════════════════════════════════════════════════════════════════
# EXCEL FILE HEADERS
# ══════════════════════════════════════════════════════════════════════════════
CLIENT_HEADERS   = ["client_id","name","mobile","email","address","username","password","status","reg_date"]
SERVICE_HEADERS  = ["service_id","name","price"]
WORK_HEADERS     = ["serial","date","client_id","client_name","service_id","service_name","quantity","price","total","notes","status"]
PAYMENT_HEADERS  = ["payment_id","client_id","client_name","invoice_no","total_amount","amount_paid","balance","payment_date","payment_method","txn_id","status"]
SETTINGS_HEADERS = ["key","value"]
INVOICE_HEADERS  = ["invoice_no","serial","client_id","client_name","date","total","status","pdf_path"]
REPORTS_HEADERS  = ["report_id","type","generated_on","file_path"]

from models.users import AdminUser, ClientUser  # noqa: F401 – re-exported for Flask-Login
from utils import db as _db

# ══════════════════════════════════════════════════════════════════════════════
# INITIALISE DIRECTORIES AND EXCEL FILES
# ══════════════════════════════════════════════════════════════════════════════
def setup_directories():
    """Create all required folders if they do not exist."""
    for folder in [config.DATA_DIR, config.INVOICES_DIR,
                   config.BACKUPS_DIR, config.UPLOADS_DIR]:
        os.makedirs(folder, exist_ok=True)
        print(f"  [OK] Folder ready: {folder}")


def setup_excel_files():
    """Create Excel files with headers if they do not exist."""
    files = {
        "clients.xlsx":      CLIENT_HEADERS,
        "services.xlsx":     SERVICE_HEADERS,
        "work_records.xlsx": WORK_HEADERS,
        "payments.xlsx":     PAYMENT_HEADERS,
        "settings.xlsx":     SETTINGS_HEADERS,
        "invoices.xlsx":     INVOICE_HEADERS,
        "reports.xlsx":      REPORTS_HEADERS,
    }
    for filename, headers in files.items():
        path = os.path.join(config.DATA_DIR, filename)
        ensure_file(path, headers)
        print(f"  [OK] Excel ready: {filename}")


def setup_default_services():
    """
    If services.xlsx is empty, insert the default 9 services.
    """
    path = os.path.join(config.DATA_DIR, "services.xlsx")
    rows = read_rows(path)
    if rows:
        return  # Already has data

    defaults = [
        ("S001","Reels Edit",                        150.0),
        ("S002","Podcast",                           200.0),
        ("S003","YouTube Shorts",                     60.0),
        ("S004","YouTube Long Video (Per 10 Minutes)",30.0),
        ("S005","Simple Photo Edit",                   5.0),
        ("S006","Professional Photo Edit",            10.0),
        ("S007","AI Generated Photo",                 17.0),
        ("S008","Content Writing",                    45.0),
        ("S009","Script + Content + Reels Edit",     175.0),
    ]
    data = [{"service_id": s[0], "name": s[1], "price": s[2]} for s in defaults]
    write_rows(path, data, SERVICE_HEADERS)
    print("  [OK] Default services inserted.")


def setup_admin_credentials():
    """
    If settings.xlsx has no admin password yet, store the default hashed password.
    """
    path = os.path.join(config.DATA_DIR, "settings.xlsx")
    rows = read_rows(path)
    keys = {r["key"] for r in rows}

    defaults = {
        "admin_username":      config.ADMIN_USERNAME,
        "admin_password_hash": generate_password_hash(config.ADMIN_DEFAULT_PASSWORD),
        "admin_email":         config.ADMIN_DEFAULT_EMAIL,   # Set via Settings page
        "contact_phone":       config.DEFAULT_PHONE,
        "contact_instagram":   config.DEFAULT_INSTAGRAM,
        "invoice_footer":      config.DEFAULT_FOOTER,
        # SMTP email settings (configure in Settings page)
        "smtp_host":           config.DEFAULT_SMTP_HOST,
        "smtp_port":           config.DEFAULT_SMTP_PORT,
        "smtp_email":          config.DEFAULT_SMTP_EMAIL,
        "smtp_password":       config.DEFAULT_SMTP_PASSWORD,
        "smtp_name":           config.DEFAULT_SMTP_NAME,
    }

    changed = False
    for k, v in defaults.items():
        if k not in keys:
            rows.append({"key": k, "value": v})
            changed = True

    # Force update to new admin defaults if settings still has old 'admin' credentials
    username_row = next((r for r in rows if r["key"] == "admin_username"), None)
    if username_row and username_row.get("value") == "admin":
        username_row["value"] = config.ADMIN_USERNAME
        password_row = next((r for r in rows if r["key"] == "admin_password_hash"), None)
        if password_row:
            password_row["value"] = generate_password_hash(config.ADMIN_DEFAULT_PASSWORD)
        changed = True

    if changed:
        write_rows(path, rows, SETTINGS_HEADERS)
        print("  [OK] Default settings written.")


# ══════════════════════════════════════════════════════════════════════════════
# CREATE FLASK APP
# ══════════════════════════════════════════════════════════════════════════════
def create_app():
    setup_directories()
    setup_excel_files()
    setup_default_services()
    setup_admin_credentials()

    # Initialize DB if DATABASE_URL is configured (optional Supabase/Postgres)
    try:
        if _db.is_enabled():
            _db.init_db()
            print("  [OK] Database initialized.")

            # Seed default settings from Excel to DB if missing
            settings_path = os.path.join(config.DATA_DIR, "settings.xlsx")
            settings_rows = read_rows(settings_path)
            for r in settings_rows:
                k = r.get("key")
                v = r.get("value", "")
                if k and not _db.get_setting(k):
                    _db.set_setting(k, v)

            # Seed default services from Excel to DB if missing
            services_path = os.path.join(config.DATA_DIR, "services.xlsx")
            services_rows = read_rows(services_path)
            db_services = _db.get_all_services()
            db_service_ids = {s["service_id"] for s in db_services}
            for s in services_rows:
                sid = s.get("service_id")
                if sid and sid not in db_service_ids:
                    _db.create_service(s)
            print("  [OK] Database seeded from Excel.")
    except Exception as e:
        print("  ! Database init failed:", e)

    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    # ── Flask-Login setup ──────────────────────────────────────────────────
    login_manager = LoginManager(app)
    login_manager.login_view      = "auth.login"
    login_manager.login_message   = "Please log in to continue."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login calls this every request to reload the user from the session.
        user_id is the string stored in the session cookie.
        """
        if user_id == "admin":
            return AdminUser()

        if _db.is_enabled():
            client_data = _db.get_client_by_id(user_id)
            if client_data:
                return ClientUser(client_data)
            return None

        # Look up client by client_id
        clients_path = os.path.join(config.DATA_DIR, "clients.xlsx")
        for c in read_rows(clients_path):
            if c.get("client_id") == user_id:
                return ClientUser(c)
        return None

    # ── Register Blueprints ────────────────────────────────────────────────
    from routes.auth   import auth
    from routes.admin  import admin
    from routes.client import client_bp

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(client_bp)

    # ── Root redirect ──────────────────────────────────────────────────────
    from flask import send_from_directory, abort

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("client.dashboard"))
        # Serve the static landing page for unauthenticated visitors
        return send_from_directory(os.path.join(app.root_path, "docs"), "index.html")

    @app.route("/<path:filename>")
    def serve_docs_assets(filename):
        """Serve static assets from the docs folder (for local development parity)."""
        docs_dir = os.path.join(app.root_path, "docs")
        file_path = os.path.join(docs_dir, filename)
        if os.path.isfile(file_path):
            return send_from_directory(docs_dir, filename)
        abort(404)

    # ── Serve uploaded files (logo, QR) ───────────────────────────────────
    from flask import send_from_directory

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        """Serve files from the uploads folder (logo, QR images)."""
        return send_from_directory(config.UPLOADS_DIR, filename)

    # ── Jinja2 globals ─────────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        """Make these variables available in every template automatically."""
        from utils.excel_manager import read_rows as _rr
        from datetime import datetime as _dt
        settings_path = os.path.join(config.DATA_DIR, "settings.xlsx")
        settings_rows = _rr(settings_path)
        settings = {r["key"]: r.get("value","") for r in settings_rows}
        return dict(
            app_name="VEMS",
            now=_dt.now(),           # Available in all templates as 'now'
            contact_phone=settings.get("contact_phone", config.DEFAULT_PHONE),
            contact_insta=settings.get("contact_instagram", config.DEFAULT_INSTAGRAM),
        )

    return app


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    # Force UTF-8 output on Windows to avoid encoding errors
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n=== Video Editing Management System (VEMS) ===")
    print("=" * 48)

    print("\n[*]  Starting Flask server...")
    print("     URL  --> http://127.0.0.1:5000")
    print("     Admin Login: umashankar / videoeditor")
    print("     Press Ctrl+C to stop.\n")

    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
