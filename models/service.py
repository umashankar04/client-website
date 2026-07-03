import os
from config import Config
from utils.excel_db import init_excel_file, read_sheet, write_sheet

SERVICES_FILE = os.path.join(Config.DATA_DIR, 'services.xlsx')
HEADERS = ['Service ID', 'Name', 'Price']

DEFAULT_SERVICES = [
    {"Name": "Reels Edit", "Price": 150.0},
    {"Name": "Podcast", "Price": 200.0},
    {"Name": "YouTube Shorts", "Price": 60.0},
    {"Name": "YouTube Long Video (Per 10 Minutes)", "Price": 30.0},
    {"Name": "Simple Photo Edit", "Price": 5.0},
    {"Name": "Professional Photo Edit", "Price": 10.0},
    {"Name": "AI Generated Photo", "Price": 17.0},
    {"Name": "Content Writing", "Price": 45.0},
    {"Name": "Script + Content + Reels Edit", "Price": 175.0}
]

def init_services():
    """Initializes services.xlsx with default values if empty."""
    init_excel_file(SERVICES_FILE, HEADERS)
    
    rows = read_sheet(SERVICES_FILE)
    if not rows:
        # Prepopulate with defaults
        for idx, svc in enumerate(DEFAULT_SERVICES, 1):
            rows.append({
                'Service ID': f"S{idx:03d}",
                'Name': svc['Name'],
                'Price': svc['Price']
            })
        write_sheet(SERVICES_FILE, rows, HEADERS)

def get_all_services():
    """Returns a list of all services."""
    init_services()
    return read_sheet(SERVICES_FILE)

def get_service_by_id(service_id):
    """Retrieves a single service record by Service ID."""
    services = get_all_services()
    for s in services:
        if s.get('Service ID') == service_id:
            return s
    return None

def generate_next_service_id():
    """Generates next Service ID (e.g. S001, S002...)."""
    services = get_all_services()
    if not services:
        return "S001"
    
    max_num = 0
    for s in services:
        s_id = s.get('Service ID', '')
        if s_id.startswith('S'):
            try:
                num = int(s_id[1:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"S{max_num + 1:03d}"

def add_service(name, price):
    """Adds a new service."""
    service_id = generate_next_service_id()
    services = get_all_services()
    
    # Ensure price is float
    try:
        f_price = float(price)
    except ValueError:
        f_price = 0.0
        
    services.append({
        'Service ID': service_id,
        'Name': name,
        'Price': f_price
    })
    write_sheet(SERVICES_FILE, services, HEADERS)
    return service_id

def edit_service(service_id, name, price):
    """Edits an existing service."""
    services = get_all_services()
    updated = False
    
    try:
        f_price = float(price)
    except ValueError:
        f_price = 0.0
        
    for s in services:
        if s.get('Service ID') == service_id:
            s['Name'] = name
            s['Price'] = f_price
            updated = True
            break
            
    if updated:
        write_sheet(SERVICES_FILE, services, HEADERS)
    return updated

def delete_service(service_id):
    """Deletes a service from services.xlsx."""
    services = get_all_services()
    new_list = [s for s in services if s.get('Service ID') != service_id]
    if len(new_list) < len(services):
        write_sheet(SERVICES_FILE, new_list, HEADERS)
        return True
    return False
