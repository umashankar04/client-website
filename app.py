import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user

from config import Config
import utils.backup_manager as backup_mgr

# Import models to trigger spreadsheet setup
import models.settings as settings_model
import models.client as client_model
import models.service as service_model
import models.work as work_model
import models.payment as payment_model
import models.invoice as invoice_model
from models.client import User

# Import Blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.client_routes import client_bp
from routes.api import api_bp

def create_app():
    """
    Bootstrap the application: initializes config, registers blueprints, 
    prepares Excel databases, and runs startup tasks.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 1. Ensure all system directories exist
    for directory in [Config.DATA_DIR, Config.UPLOADS_DIR, Config.INVOICES_DIR, Config.BACKUPS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    # 2. Initialize Excel databases with headers & default values
    settings_model.init_settings()
    client_model.init_clients()
    service_model.init_services()
    work_model.init_work()
    payment_model.init_payments()
    invoice_model.init_invoices()
    
    # 3. Create a startup automatic checkpoint backup
    try:
        backup_mgr.create_backup(is_manual=False)
    except Exception as e:
        print(f"Startup backup failed: {e}")
        
    # 4. Setup Flask-Login session managers
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this portal.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """Loads user session from settings or client worksheet."""
        if user_id == 'admin':
            admin_user = settings_model.get_setting('admin_username', 'admin')
            return User(
                user_id='admin',
                username=admin_user,
                role='admin',
                name='Administrator'
            )
            
        client = client_model.get_client_by_id(user_id)
        if client:
            return User(
                user_id=client.get('Client ID'),
                username=client.get('Username'),
                role='client',
                name=client.get('Name'),
                email=client.get('Email'),
                mobile=client.get('Mobile Number'),
                address=client.get('Address'),
                status=client.get('Status', 'Active')
            )
        return None
        
    # 5. Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(api_bp)
    
    # 6. Default root routing
    @app.route('/')
    def index():
        """Root redirect based on user role authentication."""
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('client.dashboard'))
        return redirect(url_for('auth.login'))
        
    # 7. Error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return redirect(url_for('auth.login'))
        
    return app

if __name__ == '__main__':
    app = create_app()
    # Runs on standard port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
