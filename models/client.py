import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from config import Config
from utils.excel_db import init_excel_file, read_sheet, write_sheet

CLIENTS_FILE = os.path.join(Config.DATA_DIR, 'clients.xlsx')
HEADERS = ['Client ID', 'Name', 'Mobile Number', 'Email', 'Username', 'Password', 'Address', 'Status']

class User(UserMixin):
    """
    User class representing either the Admin or a Client for Flask-Login.
    """
    def __init__(self, user_id, username, role, name="", email="", mobile="", address="", status="Active"):
        self.id = user_id
        self.username = username
        self.role = role # 'admin' or 'client'
        self.name = name
        self.email = email
        self.mobile = mobile
        self.address = address
        self.status = status

    @property
    def is_active(self):
        # Admin is always active; clients must be active to log in
        if self.role == 'admin':
            return True
        return self.status == 'Active'

def init_clients():
    """Initializes clients.xlsx if it does not exist."""
    init_excel_file(CLIENTS_FILE, HEADERS)

def get_all_clients():
    """Returns a list of all client records."""
    init_clients()
    return read_sheet(CLIENTS_FILE)

def get_client_by_id(client_id):
    """Finds a client record by Client ID."""
    clients = get_all_clients()
    for c in clients:
        if c.get('Client ID') == client_id:
            return c
    return None

def get_client_by_username(username):
    """Finds a client record by Username."""
    clients = get_all_clients()
    for c in clients:
        if str(c.get('Username')).strip().lower() == username.strip().lower():
            return c
    return None

def generate_next_client_id():
    """Generates the next sequential Client ID (e.g., C001, C002...)."""
    clients = get_all_clients()
    if not clients:
        return "C001"
    
    max_num = 0
    for c in clients:
        c_id = c.get('Client ID', '')
        if c_id.startswith('C'):
            try:
                num = int(c_id[1:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"C{max_num + 1:03d}"

def add_client(name, mobile, email, username, password, address, status='Active'):
    """Adds a new client record, hashing the password."""
    # Ensure username is unique
    if get_client_by_username(username):
        raise ValueError("Username already exists.")
        
    client_id = generate_next_client_id()
    hashed_pwd = generate_password_hash(password)
    
    clients = get_all_clients()
    new_client = {
        'Client ID': client_id,
        'Name': name,
        'Mobile Number': mobile,
        'Email': email,
        'Username': username,
        'Password': hashed_pwd,
        'Address': address,
        'Status': status
    }
    
    clients.append(new_client)
    write_sheet(CLIENTS_FILE, clients, HEADERS)
    return client_id

def edit_client(client_id, name, mobile, email, username, address, status):
    """Edits an existing client's details."""
    # Ensure username check doesn't clash with others
    existing = get_client_by_username(username)
    if existing and existing.get('Client ID') != client_id:
        raise ValueError("Username is taken by another client.")
        
    clients = get_all_clients()
    updated = False
    for c in clients:
        if c.get('Client ID') == client_id:
            c['Name'] = name
            c['Mobile Number'] = mobile
            c['Email'] = email
            c['Username'] = username
            c['Address'] = address
            c['Status'] = status
            updated = True
            break
            
    if updated:
        write_sheet(CLIENTS_FILE, clients, HEADERS)
    return updated

def reset_password(client_id, new_password):
    """Resets client password to a new hashed password."""
    clients = get_all_clients()
    updated = False
    for c in clients:
        if c.get('Client ID') == client_id:
            c['Password'] = generate_password_hash(new_password)
            updated = True
            break
            
    if updated:
        write_sheet(CLIENTS_FILE, clients, HEADERS)
    return updated

def delete_client(client_id):
    """Deletes a client record from clients.xlsx."""
    clients = get_all_clients()
    new_list = [c for c in clients if c.get('Client ID') != client_id]
    if len(new_list) < len(clients):
        write_sheet(CLIENTS_FILE, new_list, HEADERS)
        return True
    return False

def toggle_client_status(client_id):
    """Toggles client status between Active and Deactivated."""
    clients = get_all_clients()
    updated = False
    for c in clients:
        if c.get('Client ID') == client_id:
            c['Status'] = 'Deactivated' if c.get('Status') == 'Active' else 'Active'
            updated = True
            break
            
    if updated:
        write_sheet(CLIENTS_FILE, clients, HEADERS)
    return updated
