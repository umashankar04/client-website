import os

# ─────────────────────────────────────────────
# Base directory = folder where this file lives
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Where Excel files are stored
DATA_DIR = os.path.join(BASE_DIR, "data")

# Where PDF invoices are saved
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")

# Where zip backups are saved
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

# Where logo / QR images are uploaded
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Flask secret key for sessions
SECRET_KEY = "vems-super-secret-2024-key-xz99"

# Default admin credentials
ADMIN_USERNAME = "umashankar"
ADMIN_DEFAULT_PASSWORD = "videoeditor"
ADMIN_DEFAULT_EMAIL = ""           # Set your Gmail in Settings page

# SMTP / Email defaults (configured via Settings page)
DEFAULT_SMTP_HOST     = "smtp.gmail.com"
DEFAULT_SMTP_PORT     = "587"
DEFAULT_SMTP_EMAIL    = ""         # Your Gmail address
DEFAULT_SMTP_PASSWORD = ""         # Your Gmail App Password (not regular password)
DEFAULT_SMTP_NAME     = "VEMS"     # Sender name shown in email

# Contact info defaults
DEFAULT_PHONE     = "9668797558"
DEFAULT_INSTAGRAM = "https://www.instagram.com/pradhan04_"
DEFAULT_FOOTER    = "Thank you for your business! Call 9668797558 for any queries."

class Config:
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    INVOICES_DIR = INVOICES_DIR
    BACKUPS_DIR = BACKUPS_DIR
    UPLOADS_DIR = UPLOADS_DIR
    SECRET_KEY = SECRET_KEY

