"""
utils/backup.py
───────────────
Create and restore ZIP backups of the /data folder.
"""

import os
import zipfile
import shutil
from datetime import datetime
import config


def create_backup():
    """
    Zip all Excel files in the data folder and save to /backups.
    Returns the backup filename on success.
    """
    os.makedirs(config.BACKUPS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.zip"
    filepath = os.path.join(config.BACKUPS_DIR, filename)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add every file inside /data
        if os.path.exists(config.DATA_DIR):
            for fname in os.listdir(config.DATA_DIR):
                full = os.path.join(config.DATA_DIR, fname)
                if os.path.isfile(full):
                    zf.write(full, fname)  # Store with just filename (no path)

    return filename


def list_backups():
    """
    Return list of backup info dicts sorted newest first.
    Each dict has: filename, created_at, size_kb
    """
    if not os.path.exists(config.BACKUPS_DIR):
        return []

    result = []
    for fname in os.listdir(config.BACKUPS_DIR):
        if fname.endswith(".zip"):
            fpath = os.path.join(config.BACKUPS_DIR, fname)
            stat = os.stat(fpath)
            result.append({
                "filename": fname,
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size_kb": round(stat.st_size / 1024, 1),
            })

    result.sort(key=lambda x: x["filename"], reverse=True)
    return result


def restore_backup(filename):
    """
    Extract a backup ZIP back into the /data folder.
    Current data files are overwritten.
    """
    filepath = os.path.join(config.BACKUPS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Backup not found: {filename}")

    os.makedirs(config.DATA_DIR, exist_ok=True)

    with zipfile.ZipFile(filepath, "r") as zf:
        zf.extractall(config.DATA_DIR)
