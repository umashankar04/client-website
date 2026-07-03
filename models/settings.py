import os
from werkzeug.security import generate_password_hash
from config import Config
from utils.excel_db import init_excel_file, read_sheet, write_sheet

SETTINGS_FILE = os.path.join(Config.DATA_DIR, 'settings.xlsx')
HEADERS = ['Key', 'Value']

def init_settings():
    """
    Initializes settings.xlsx with default values if not present.
    """
    init_excel_file(SETTINGS_FILE, HEADERS)
    
    # Read existing settings
    rows = read_sheet(SETTINGS_FILE)
    keys = {row['Key'] for row in rows}
    
    defaults = {
        'admin_username': 'admin',
        # Default password is 'admin123'
        'admin_password': generate_password_hash('admin123'),
        'contact_number': '9668797558',
        'instagram_link': 'https://www.instagram.com/pradhan04_',
        'invoice_footer': 'Thank you for your business! Call 9668797558 for inquiries.',
        'logo_path': '',
        'qr_code_path': ''
    }
    
    updated = False
    for k, v in defaults.items():
        if k not in keys:
            rows.append({'Key': k, 'Value': v})
            updated = True
            
    if updated:
        write_sheet(SETTINGS_FILE, rows, HEADERS)

def get_setting(key, default=''):
    """
    Gets the value of a setting by its key.
    """
    rows = read_sheet(SETTINGS_FILE)
    for row in rows:
        if row.get('Key') == key:
            return row.get('Value') or default
    return default

def set_setting(key, value):
    """
    Sets the value of a setting.
    """
    rows = read_sheet(SETTINGS_FILE)
    found = False
    for row in rows:
        if row.get('Key') == key:
            row['Value'] = value
            found = True
            break
            
    if not found:
        rows.append({'Key': key, 'Value': value})
        
    write_sheet(SETTINGS_FILE, rows, HEADERS)
    return True

def get_all_settings():
    """
    Returns a dictionary of all settings.
    """
    rows = read_sheet(SETTINGS_FILE)
    settings_dict = {}
    for row in rows:
        settings_dict[row.get('Key')] = row.get('Value', '')
    return settings_dict
