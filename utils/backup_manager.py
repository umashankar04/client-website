import os
import zipfile
import shutil
from datetime import datetime
from config import Config

def create_backup(is_manual=False):
    """
    Creates a zip backup of the data folder and saves it in the backups directory.
    Filenames are formatted with date and time: backup_YYYYMMDD_HHMMSS.zip
    """
    # Ensure directories exist
    if not os.path.exists(Config.BACKUPS_DIR):
        os.makedirs(Config.BACKUPS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "manual" if is_manual else "auto"
    backup_filename = f"backup_{prefix}_{timestamp}.zip"
    backup_path = os.path.join(Config.BACKUPS_DIR, backup_filename)
    
    # Zip the data folder
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(Config.DATA_DIR):
            for root, dirs, files in os.walk(Config.DATA_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, Config.DATA_DIR)
                    zipf.write(file_path, os.path.join('data', arcname))
        
        # Also include uploaded assets like QR codes and logos
        if os.path.exists(Config.UPLOADS_DIR):
            for root, dirs, files in os.walk(Config.UPLOADS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, Config.UPLOADS_DIR)
                    zipf.write(file_path, os.path.join('uploads', arcname))
                    
    return backup_filename

def get_all_backups():
    """
    Returns a list of all backup files sorted by creation date (newest first).
    """
    if not os.path.exists(Config.BACKUPS_DIR):
        return []
    
    backups = []
    for file in os.listdir(Config.BACKUPS_DIR):
        if file.endswith('.zip') and file.startswith('backup_'):
            file_path = os.path.join(Config.BACKUPS_DIR, file)
            stat = os.stat(file_path)
            created_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_mb = round(stat.st_size / (1024 * 1024), 2)
            backups.append({
                'filename': file,
                'created_at': created_time,
                'size': f"{size_mb} MB" if size_mb > 0 else f"{round(stat.st_size/1024, 2)} KB"
            })
            
    # Sort by filename descending (since filenames contain timestamps)
    backups.sort(key=lambda x: x['filename'], reverse=True)
    return backups

def restore_backup(backup_filename):
    """
    Restores the system from a specific backup file.
    Before restoring, it takes a quick auto-backup of the current state.
    """
    backup_path = os.path.join(Config.BACKUPS_DIR, backup_filename)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file {backup_filename} not found.")
        
    # Take a temporary safety backup
    create_backup(is_manual=False)
    
    # Extract backup file to temporary directory
    temp_extract_dir = os.path.join(Config.BACKUPS_DIR, 'temp_restore')
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir)
    
    with zipfile.ZipFile(backup_path, 'r') as zipf:
        zipf.extractall(temp_extract_dir)
        
    # Copy files back to data and uploads directories
    restored_data_dir = os.path.join(temp_extract_dir, 'data')
    if os.path.exists(restored_data_dir):
        # Clear current data folder
        if os.path.exists(Config.DATA_DIR):
            shutil.rmtree(Config.DATA_DIR)
        shutil.copytree(restored_data_dir, Config.DATA_DIR)
        
    restored_uploads_dir = os.path.join(temp_extract_dir, 'uploads')
    if os.path.exists(restored_uploads_dir):
        # Merge/Restore uploads
        if not os.path.exists(Config.UPLOADS_DIR):
            os.makedirs(Config.UPLOADS_DIR)
        for item in os.listdir(restored_uploads_dir):
            s = os.path.join(restored_uploads_dir, item)
            d = os.path.join(Config.UPLOADS_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
    # Clean up temp folder
    shutil.rmtree(temp_extract_dir)
    return True
