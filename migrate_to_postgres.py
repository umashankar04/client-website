"""
migrate_to_postgres.py
──────────────────────
Migrates settings.xlsx and clients.xlsx records to the SQL Database.
Run with: python migrate_to_postgres.py
"""
import os
import sys
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from utils import db as _db
from utils.excel_manager import read_rows
import config

CLIENTS_FILE = os.path.join(config.DATA_DIR, "clients.xlsx")
SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.xlsx")

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
                # Check if it already exists to avoid overwriting/duplicates
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

            # Check if client already exists in DB
            if not _db.get_client_by_name(name):
                # Format to match DB schema dictionary input
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

    print("\n[SUCCESS] Migration complete!")

if __name__ == "__main__":
    migrate()
