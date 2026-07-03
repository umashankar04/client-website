import os
from datetime import datetime
from config import Config
from utils.excel_db import init_excel_file, read_sheet, write_sheet
import models.work as work_model

INVOICES_FILE = os.path.join(Config.DATA_DIR, 'invoices.xlsx')
HEADERS = ['Invoice Number', 'Work Serial Number', 'Client ID', 'Date', 'Total', 'File Path']

def init_invoices():
    """Initializes invoices.xlsx if it does not exist."""
    init_excel_file(INVOICES_FILE, HEADERS)

def get_all_invoices():
    """Returns a list of all invoice records."""
    init_invoices()
    return read_sheet(INVOICES_FILE)

def get_invoice_by_no(invoice_no):
    """Finds an invoice record by Invoice Number."""
    invoices = get_all_invoices()
    for inv in invoices:
        if inv.get('Invoice Number') == invoice_no:
            return inv
    return None

def get_invoice_by_work(work_serial):
    """Finds an invoice record by Work Serial Number."""
    invoices = get_all_invoices()
    for inv in invoices:
        if inv.get('Work Serial Number') == work_serial:
            return inv
    return None

def get_invoices_by_client(client_id):
    """Finds all invoices for a specific client."""
    invoices = get_all_invoices()
    return [inv for inv in invoices if inv.get('Client ID') == client_id]

def generate_next_invoice_no():
    """Generates the next Invoice Number (e.g., INV-0001, INV-0002...)."""
    invoices = get_all_invoices()
    if not invoices:
        return "INV-0001"
    
    max_num = 0
    for inv in invoices:
        inv_no = inv.get('Invoice Number', '')
        if inv_no.startswith('INV-'):
            try:
                num = int(inv_no[4:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"INV-{max_num + 1:04d}"

def create_invoice_record(work_serial, file_path):
    """
    Creates an invoice entry in the spreadsheet after a PDF is generated.
    Returns the generated Invoice Number.
    """
    # Check if invoice record already exists for this work serial
    existing = get_invoice_by_work(work_serial)
    if existing:
        # Just update file path and return the existing invoice number
        invoices = get_all_invoices()
        for inv in invoices:
            if inv.get('Work Serial Number') == work_serial:
                inv['File Path'] = file_path
                inv['Date'] = datetime.now().strftime('%Y-%m-%d')
                break
        write_sheet(INVOICES_FILE, invoices, HEADERS)
        return existing.get('Invoice Number')

    work = work_model.get_work_by_serial(work_serial)
    if not work:
        raise ValueError(f"Work entry {work_serial} not found.")

    invoice_no = generate_next_invoice_no()
    invoices = get_all_invoices()
    
    new_invoice = {
        'Invoice Number': invoice_no,
        'Work Serial Number': work_serial,
        'Client ID': work.get('Client ID'),
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Total': work.get('Total'),
        'File Path': file_path
    }
    
    invoices.append(new_invoice)
    write_sheet(INVOICES_FILE, invoices, HEADERS)
    return invoice_no

def delete_invoice_record(invoice_no):
    """Deletes an invoice record."""
    invoices = get_all_invoices()
    new_list = [inv for inv in invoices if inv.get('Invoice Number') != invoice_no]
    if len(new_list) < len(invoices):
        write_sheet(INVOICES_FILE, new_list, HEADERS)
        return True
    return False
