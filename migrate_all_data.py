"""
migrate_all_data.py
───────────────────
Migrates all local Excel database records (Settings, Clients, Services, Work Records, Payments, Invoices, and Reports) to the SQL Database.
Run with: python migrate_all_data.py
"""
import os
import sys
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from utils import db as _db
from utils.excel_manager import read_rows
import config

CLIENTS_FILE  = os.path.join(config.DATA_DIR, "clients.xlsx")
SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.xlsx")
SERVICES_FILE = os.path.join(config.DATA_DIR, "services.xlsx")
WORK_FILE     = os.path.join(config.DATA_DIR, "work_records.xlsx")
PAYMENTS_FILE = os.path.join(config.DATA_DIR, "payments.xlsx")
INVOICES_FILE = os.path.join(config.DATA_DIR, "invoices.xlsx")
REPORTS_FILE  = os.path.join(config.DATA_DIR, "reports.xlsx")

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def migrate():
    if not _db.is_enabled():
        print("[-] DATABASE_URL is not set or database is disabled. Exiting.")
        sys.exit(1)

    print("[*] Initializing Database schema...")
    _db.init_db()
    print("[OK] Database initialized.")

    # 1. Migrate settings
    print("[*] Migrating settings...")
    try:
        settings = read_rows(SETTINGS_FILE)
        migrated_settings = 0
        for s in settings:
            key = s.get("key")
            value = s.get("value") or ""
            if key:
                if not _db.get_setting(key):
                    _db.set_setting(key, value)
                    migrated_settings += 1
        print(f"[OK] Migrated {migrated_settings} settings.")
    except Exception as e:
        print(f"[!] Failed to migrate settings: {e}")

    # 2. Migrate clients
    print("[*] Migrating clients...")
    try:
        clients = read_rows(CLIENTS_FILE)
        migrated_clients = 0
        for c in clients:
            client_id = c.get("client_id")
            name = c.get("name")
            if not client_id or not name:
                continue

            if not _db.get_client_by_name(name):
                db_data = {
                    "client_id": client_id,
                    "name": name,
                    "mobile": c.get("mobile") or "",
                    "email": c.get("email") or "",
                    "address": c.get("address") or "",
                    "username": c.get("username") or "",
                    "password": c.get("password") or "",
                    "status": c.get("status") or "Active",
                    "reg_date": c.get("reg_date") or ""
                }
                _db.create_client(db_data)
                migrated_clients += 1
        print(f"[OK] Migrated {migrated_clients} clients.")
    except Exception as e:
        print(f"[!] Failed to migrate clients: {e}")

    # 3. Migrate services
    print("[*] Migrating services...")
    try:
        services = read_rows(SERVICES_FILE)
        migrated_services = 0
        for s in services:
            service_id = s.get("service_id")
            name = s.get("name")
            if not service_id or not name:
                continue

            if not _db.get_service_by_id(service_id):
                db_data = {
                    "service_id": service_id,
                    "name": name,
                    "price": safe_float(s.get("price"))
                }
                _db.create_service(db_data)
                migrated_services += 1
        print(f"[OK] Migrated {migrated_services} services.")
    except Exception as e:
        print(f"[!] Failed to migrate services: {e}")

    # 4. Migrate work records
    print("[*] Migrating work records...")
    try:
        works = read_rows(WORK_FILE)
        migrated_works = 0
        for w in works:
            serial = w.get("serial")
            if not serial:
                continue

            if not _db.get_work_by_serial(serial):
                db_data = {
                    "serial": serial,
                    "date": w.get("date") or "",
                    "client_id": w.get("client_id") or "",
                    "client_name": w.get("client_name") or "",
                    "service_id": w.get("service_id") or "",
                    "service_name": w.get("service_name") or "",
                    "quantity": safe_int(w.get("quantity"), 1),
                    "price": safe_float(w.get("price")),
                    "total": safe_float(w.get("total")),
                    "notes": w.get("notes") or "",
                    "status": w.get("status") or "Pending"
                }
                _db.create_work(db_data)
                migrated_works += 1
        print(f"[OK] Migrated {migrated_works} work records.")
    except Exception as e:
        print(f"[!] Failed to migrate work records: {e}")

    # 5. Migrate payments
    print("[*] Migrating payments...")
    try:
        payments = read_rows(PAYMENTS_FILE)
        migrated_payments = 0
        for p in payments:
            payment_id = p.get("payment_id")
            if not payment_id:
                continue

            if not _db.get_payment_by_id(payment_id):
                db_data = {
                    "payment_id": payment_id,
                    "client_id": p.get("client_id") or "",
                    "client_name": p.get("client_name") or "",
                    "invoice_no": p.get("invoice_no") or "",
                    "total_amount": safe_float(p.get("total_amount")),
                    "amount_paid": safe_float(p.get("amount_paid")),
                    "balance": safe_float(p.get("balance")),
                    "payment_date": p.get("payment_date") or "",
                    "payment_method": p.get("payment_method") or "UPI",
                    "txn_id": p.get("txn_id") or "",
                    "status": p.get("status") or "Paid"
                }
                _db.create_payment(db_data)
                migrated_payments += 1
        print(f"[OK] Migrated {migrated_payments} payments.")
    except Exception as e:
        print(f"[!] Failed to migrate payments: {e}")

    # 6. Migrate invoices
    print("[*] Migrating invoices...")
    try:
        invoices = read_rows(INVOICES_FILE)
        migrated_invoices = 0
        for inv in invoices:
            invoice_no = inv.get("invoice_no")
            if not invoice_no:
                continue

            if not _db.get_invoice_by_no(invoice_no):
                db_data = {
                    "invoice_no": invoice_no,
                    "serial": inv.get("serial") or "",
                    "client_id": inv.get("client_id") or "",
                    "client_name": inv.get("client_name") or "",
                    "date": inv.get("date") or "",
                    "total": safe_float(inv.get("total")),
                    "status": inv.get("status") or "Pending",
                    "pdf_path": inv.get("pdf_path") or ""
                }
                _db.create_invoice(db_data)
                migrated_invoices += 1
        print(f"[OK] Migrated {migrated_invoices} invoices.")
    except Exception as e:
        print(f"[!] Failed to migrate invoices: {e}")

    # 7. Migrate reports
    print("[*] Migrating reports...")
    try:
        reports = read_rows(REPORTS_FILE)
        migrated_reports = 0
        for r in reports:
            report_id = r.get("report_id")
            if not report_id:
                continue

            existing = _db.get_all_reports()
            already_exists = any(db_rep.get("report_id") == report_id for db_rep in existing)
            if not already_exists:
                db_data = {
                    "report_id": report_id,
                    "type": r.get("type") or "",
                    "generated_on": r.get("generated_on") or "",
                    "file_path": r.get("file_path") or ""
                }
                _db.create_report(db_data)
                migrated_reports += 1
        print(f"[OK] Migrated {migrated_reports} reports.")
    except Exception as e:
        print(f"[!] Failed to migrate reports: {e}")

    print("\n[SUCCESS] All data successfully transferred to local MySQL!")

if __name__ == "__main__":
    migrate()
