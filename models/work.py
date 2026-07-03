import os
from datetime import datetime
from config import Config
from utils.excel_db import init_excel_file, read_sheet, write_sheet
import models.client as client_model
import models.service as service_model

WORK_FILE = os.path.join(Config.DATA_DIR, 'work_records.xlsx')
HEADERS = ['Serial Number', 'Date', 'Client ID', 'Client Name', 'Service ID', 'Service Type', 'Quantity', 'Price', 'Total', 'Notes', 'Status']

def init_work():
    """Initializes work_records.xlsx if it does not exist."""
    init_excel_file(WORK_FILE, HEADERS)

def get_all_work():
    """Returns a list of all work records."""
    init_work()
    return read_sheet(WORK_FILE)

def get_work_by_serial(serial):
    """Finds a work record by Serial Number."""
    works = get_all_work()
    for w in works:
        if w.get('Serial Number') == serial:
            return w
    return None

def get_work_by_client(client_id):
    """Gets all work records for a specific client."""
    works = get_all_work()
    return [w for w in works if w.get('Client ID') == client_id]

def generate_next_serial():
    """Generates the next Serial Number (e.g., W0001, W0002...)."""
    works = get_all_work()
    if not works:
        return "W0001"
    
    max_num = 0
    for w in works:
        serial = w.get('Serial Number', '')
        if serial.startswith('W'):
            try:
                num = int(serial[1:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"W{max_num + 1:04d}"

def add_work(date_str, client_id, service_id, quantity, price, notes, status='Pending'):
    """
    Adds a new work record, fetching metadata from client and service, 
    calculating total and saving to Excel.
    """
    serial = generate_next_serial()
    
    # Resolve names
    client = client_model.get_client_by_id(client_id)
    client_name = client.get('Name', 'Unknown') if client else 'Unknown'
    
    service = service_model.get_service_by_id(service_id)
    service_type = service.get('Name', 'Unknown') if service else 'Unknown'
    
    # Date formatting
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    try:
        qty = int(quantity)
    except ValueError:
        qty = 1
        
    try:
        prc = float(price)
    except ValueError:
        prc = float(service.get('Price', 0.0)) if service else 0.0
        
    total = qty * prc
    
    works = get_all_work()
    new_work = {
        'Serial Number': serial,
        'Date': date_str,
        'Client ID': client_id,
        'Client Name': client_name,
        'Service ID': service_id,
        'Service Type': service_type,
        'Quantity': qty,
        'Price': prc,
        'Total': total,
        'Notes': notes,
        'Status': status
    }
    
    works.append(new_work)
    write_sheet(WORK_FILE, works, HEADERS)
    return serial

def edit_work(serial, date_str, client_id, service_id, quantity, price, notes, status):
    """Edits an existing work record, updating client/service details and recalculating total."""
    works = get_all_work()
    updated = False
    
    # Resolve names
    client = client_model.get_client_by_id(client_id)
    client_name = client.get('Name', 'Unknown') if client else 'Unknown'
    
    service = service_model.get_service_by_id(service_id)
    service_type = service.get('Name', 'Unknown') if service else 'Unknown'
    
    try:
        qty = int(quantity)
    except ValueError:
        qty = 1
        
    try:
        prc = float(price)
    except ValueError:
        prc = 0.0
        
    total = qty * prc
    
    for w in works:
        if w.get('Serial Number') == serial:
            w['Date'] = date_str
            w['Client ID'] = client_id
            w['Client Name'] = client_name
            w['Service ID'] = service_id
            w['Service Type'] = service_type
            w['Quantity'] = qty
            w['Price'] = prc
            w['Total'] = total
            w['Notes'] = notes
            w['Status'] = status
            updated = True
            break
            
    if updated:
        write_sheet(WORK_FILE, works, HEADERS)
    return updated

def delete_work(serial):
    """Deletes a work record."""
    works = get_all_work()
    new_list = [w for w in works if w.get('Serial Number') != serial]
    if len(new_list) < len(works):
        write_sheet(WORK_FILE, new_list, HEADERS)
        return True
    return False

def update_work_status(serial, status):
    """Updates only the status of a work entry."""
    works = get_all_work()
    updated = False
    for w in works:
        if w.get('Serial Number') == serial:
            w['Status'] = status
            updated = True
            break
    if updated:
        write_sheet(WORK_FILE, works, HEADERS)
    return updated
