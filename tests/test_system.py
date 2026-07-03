import os
import unittest
import shutil
from datetime import datetime
from config import Config

# Configure test directories to avoid overwriting production data
Config.DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
Config.INVOICES_DIR = os.path.join(os.path.dirname(__file__), 'test_invoices')
Config.BACKUPS_DIR = os.path.join(os.path.dirname(__file__), 'test_backups')
Config.UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'test_uploads')

import models.settings as settings_model
import models.client as client_model
import models.service as service_model
import models.work as work_model
import models.payment as payment_model
import models.invoice as invoice_model
import utils.backup_manager as backup_mgr
import utils.pdf_generator as pdf_gen

class TestVEMSSystem(unittest.TestCase):
    """
    Test suite to verify VEMS backend logic, database, calculations, and PDF reporting.
    """
    
    @classmethod
    def setUpClass(cls):
        # Create directories
        for d in [Config.DATA_DIR, Config.INVOICES_DIR, Config.BACKUPS_DIR, Config.UPLOADS_DIR]:
            if not os.path.exists(d):
                os.makedirs(d)
                
        # Initialize worksheets
        settings_model.init_settings()
        client_model.init_clients()
        service_model.init_services()
        work_model.init_work()
        payment_model.init_payments()
        invoice_model.init_invoices()

    @classmethod
    def tearDownClass(cls):
        # Clean up test directories
        for d in [Config.DATA_DIR, Config.INVOICES_DIR, Config.BACKUPS_DIR, Config.UPLOADS_DIR]:
            if os.path.exists(d):
                shutil.rmtree(d)

    def test_01_settings(self):
        """Test reading and writing settings."""
        settings_model.set_setting('test_key', 'test_value')
        val = settings_model.get_setting('test_key')
        self.assertEqual(val, 'test_value')
        
        # Test defaults
        contact = settings_model.get_setting('contact_number')
        self.assertEqual(contact, '9668797558')

    def test_02_clients(self):
        """Test Client account creations and lookups."""
        client_id = client_model.add_client(
            name="John Doe",
            mobile="9876543210",
            email="john@doe.com",
            username="johndoe",
            password="password123",
            address="123 Street",
            status="Active"
        )
        self.assertEqual(client_id, "C001")
        
        # Verify duplicate usernames raise error
        with self.assertRaises(ValueError):
            client_model.add_client(
                name="Duplicate User",
                mobile="1111111111",
                email="dup@user.com",
                username="johndoe",
                password="password111",
                address="Address"
            )
            
        # Verify client getters
        client = client_model.get_client_by_id("C001")
        self.assertIsNotNone(client)
        self.assertEqual(client['Name'], "John Doe")
        
        client_by_user = client_model.get_client_by_username("johndoe")
        self.assertIsNotNone(client_by_user)

    def test_03_services(self):
        """Test standard services and customized prices."""
        # Test prepopulated services
        services = service_model.get_all_services()
        self.assertGreater(len(services), 0)
        
        # Test add new service
        svc_id = service_model.add_service("VFX Advanced Edit", 550.0)
        svc = service_model.get_service_by_id(svc_id)
        self.assertIsNotNone(svc)
        self.assertEqual(svc['Name'], "VFX Advanced Edit")
        self.assertEqual(float(svc['Price']), 550.0)

    def test_04_work_entries(self):
        """Test logging work, auto serial codes, and totals."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Client C001, Service Reels Edit (₹150.00 standard rate)
        serial = work_model.add_work(
            date_str=today,
            client_id="C001",
            service_id="S001", # Reels Edit
            quantity=3,
            price=150.00,
            notes="Testing Reels",
            status="Pending"
        )
        self.assertEqual(serial, "W0001")
        
        work_entry = work_model.get_work_by_serial("W0001")
        self.assertIsNotNone(work_entry)
        self.assertEqual(float(work_entry['Total']), 450.00) # 3 * 150
        self.assertEqual(work_entry['Status'], "Pending")

    def test_05_payments_and_status(self):
        """Test recording payments and checking state triggers (Pending -> Partial -> Paid)."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 1. Record partial payment of ₹200.00 (Outstanding was ₹450.00)
        payment_model.add_payment(
            work_serial="W0001",
            date_str=today,
            amount=200.00,
            transaction_id="TXN10001",
            payment_method="UPI"
        )
        
        # Check work status - should become Partial Payment
        work_entry = work_model.get_work_by_serial("W0001")
        self.assertEqual(work_entry['Status'], "Partial Payment")
        
        # 2. Settle remaining ₹250.00 balance
        payment_model.add_payment(
            work_serial="W0001",
            date_str=today,
            amount=250.00,
            transaction_id="TXN10002",
            payment_method="Bank Transfer"
        )
        
        # Check work status - should become Paid
        work_entry = work_model.get_work_by_serial("W0001")
        self.assertEqual(work_entry['Status'], "Paid")
        
        # Check payment logs
        pmts = payment_model.get_payments_by_work("W0001")
        self.assertEqual(len(pmts), 2)
        total_paid = payment_model.get_total_paid_for_work("W0001")
        self.assertEqual(total_paid, 450.00)

    def test_06_pdf_invoice(self):
        """Test invoice creation with ReportLab flowables."""
        work = work_model.get_work_by_serial("W0001")
        client = client_model.get_client_by_id("C001")
        
        invoice_no = "INV-0001"
        pdf_path = os.path.join(Config.INVOICES_DIR, f"{invoice_no}.pdf")
        
        invoice_data = {
            'invoice_no': invoice_no,
            'client_name': client['Name'],
            'client_mobile': client['Mobile Number'],
            'client_email': client['Email'],
            'client_address': client['Address'],
            'date': work['Date'],
            'service_name': work['Service Type'],
            'quantity': work['Quantity'],
            'price': float(work['Price']),
            'total': float(work['Total']),
            'payment_status': work['Status'],
            'amount_paid': 450.00,
            'remaining_balance': 0.0,
            'payment_method': 'Bank Transfer',
            'transaction_id': 'TXN10002'
        }
        
        success = pdf_gen.generate_invoice_pdf(
            invoice_data=invoice_data,
            output_path=pdf_path,
            footer_text="Test Footer"
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000) # Verify it has content

    def test_07_backup(self):
        """Test data archiving zip files."""
        backup_file = backup_mgr.create_backup(is_manual=True)
        self.assertTrue(backup_file.startswith("backup_manual_"))
        
        backups_list = backup_mgr.get_all_backups()
        self.assertGreater(len(backups_list), 0)

if __name__ == '__main__':
    unittest.main()
