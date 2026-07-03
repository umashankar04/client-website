import os
from datetime import datetime
from config import Config
from utils.excel_db import init_excel_file, read_sheet, write_sheet
import models.work as work_model

PAYMENTS_FILE = os.path.join(Config.DATA_DIR, 'payments.xlsx')
HEADERS = ['Payment ID', 'Work Serial Number', 'Payment Date', 'Amount Paid', 'Remaining Balance', 'Transaction ID', 'Payment Method']

def init_payments():
    """Initializes payments.xlsx if it does not exist."""
    init_excel_file(PAYMENTS_FILE, HEADERS)

def get_all_payments():
    """Returns a list of all payments."""
    init_payments()
    return read_sheet(PAYMENTS_FILE)

def get_payments_by_work(work_serial):
    """Finds all payments made for a specific work entry."""
    payments = get_all_payments()
    return [p for p in payments if p.get('Work Serial Number') == work_serial]

def get_total_paid_for_work(work_serial):
    """Calculates the sum of payments recorded for a work entry."""
    work_payments = get_payments_by_work(work_serial)
    total = 0.0
    for p in work_payments:
        try:
            total += float(p.get('Amount Paid', 0.0))
        except ValueError:
            pass
    return total

def generate_next_payment_id():
    """Generates the next Payment ID (e.g., P0001, P0002...)."""
    payments = get_all_payments()
    if not payments:
        return "P0001"
    
    max_num = 0
    for p in payments:
        p_id = p.get('Payment ID', '')
        if p_id.startswith('P'):
            try:
                num = int(p_id[1:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"P{max_num + 1:04d}"

def add_payment(work_serial, date_str, amount, transaction_id, payment_method):
    """
    Records a payment transaction. Updates the remaining balance 
    and updates the associated work entry status accordingly.
    """
    work = work_model.get_work_by_serial(work_serial)
    if not work:
        raise ValueError(f"Work entry {work_serial} not found.")
        
    try:
        work_total = float(work.get('Total', 0.0))
    except ValueError:
        work_total = 0.0
        
    try:
        amount_paid = float(amount)
    except ValueError:
        amount_paid = 0.0
        
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    # Get how much has already been paid BEFORE this transaction
    already_paid = get_total_paid_for_work(work_serial)
    new_total_paid = already_paid + amount_paid
    remaining_balance = work_total - new_total_paid
    
    payment_id = generate_next_payment_id()
    payments = get_all_payments()
    
    new_payment = {
        'Payment ID': payment_id,
        'Work Serial Number': work_serial,
        'Payment Date': date_str,
        'Amount Paid': amount_paid,
        'Remaining Balance': remaining_balance,
        'Transaction ID': transaction_id,
        'Payment Method': payment_method
    }
    
    payments.append(new_payment)
    write_sheet(PAYMENTS_FILE, payments, HEADERS)
    
    # Update work status in work_records.xlsx
    new_status = 'Pending'
    if remaining_balance <= 0.05: # Float tolerance for 0
        new_status = 'Paid'
    elif new_total_paid > 0:
        new_status = 'Partial Payment'
        
    work_model.update_work_status(work_serial, new_status)
    return payment_id

def delete_payments_for_work(work_serial):
    """Deletes all payments associated with a work entry."""
    payments = get_all_payments()
    new_list = [p for p in payments if p.get('Work Serial Number') != work_serial]
    if len(new_list) < len(payments):
        write_sheet(PAYMENTS_FILE, new_list, HEADERS)
        return True
    return False

def delete_payment(payment_id):
    """Deletes a specific payment transaction and updates work status."""
    payments = get_all_payments()
    payment_to_del = None
    for p in payments:
        if p.get('Payment ID') == payment_id:
            payment_to_del = p
            break
            
    if not payment_to_del:
        return False
        
    work_serial = payment_to_del.get('Work Serial Number')
    new_list = [p for p in payments if p.get('Payment ID') != payment_id]
    write_sheet(PAYMENTS_FILE, new_list, HEADERS)
    
    # Recalculate and update work status
    work = work_model.get_work_by_serial(work_serial)
    if work:
        try:
            work_total = float(work.get('Total', 0.0))
        except ValueError:
            work_total = 0.0
            
        new_total_paid = get_total_paid_for_work(work_serial)
        remaining_balance = work_total - new_total_paid
        
        new_status = 'Pending'
        if remaining_balance <= 0.05:
            new_status = 'Paid'
        elif new_total_paid > 0:
            new_status = 'Partial Payment'
            
        work_model.update_work_status(work_serial, new_status)
        
    return True
