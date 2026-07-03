"""
models/users.py
───────────────
Flask-Login User classes.
Keeping them in a separate file breaks circular imports.
"""

import os
from flask_login import UserMixin


class AdminUser(UserMixin):
    """The single admin account."""
    def __init__(self):
        self.id   = "admin"
        self.role = "admin"
        self.name = "Administrator"


class ClientUser(UserMixin):
    """A client user loaded from clients.xlsx."""
    def __init__(self, data: dict):
        self.id       = data.get("client_id")
        self.role     = "client"
        self.name     = data.get("name", "")
        self.username = data.get("username", "")
        self.email    = data.get("email", "")
        self.mobile   = data.get("mobile", "")
        self.status   = data.get("status", "Active")
