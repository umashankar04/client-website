"""
utils/helpers.py
────────────────
Small helper functions used across the application.
"""

from datetime import datetime, date


def today_str():
    """Return today's date as YYYY-MM-DD string."""
    return date.today().strftime("%Y-%m-%d")


def now_str():
    """Return current datetime as YYYY-MM-DD HH:MM string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def safe_float(value, default=0.0):
    """Convert a value to float safely. Returns default if conversion fails."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """Convert a value to int safely. Returns default if conversion fails."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def generate_id(prefix, existing_rows, id_field):
    """
    Generate the next sequential ID.
    Example: prefix='C', existing rows with IDs ['C001','C002'] → returns 'C003'
    """
    max_num = 0
    for row in existing_rows:
        raw = str(row.get(id_field, ""))
        if raw.startswith(prefix):
            try:
                num = int(raw[len(prefix):])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"{prefix}{max_num + 1:03d}"


def format_currency(amount):
    """Format a number as Indian Rupee string. E.g. 1500.0 → '₹1,500.00'"""
    try:
        return f"₹{float(amount):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"
