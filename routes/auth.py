"""
routes/auth.py
──────────────
Password-based authentication flow for both Admin and Clients.
OTP system has been completely removed.
"""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models.users import AdminUser, ClientUser
from utils.excel_manager import read_rows, write_rows
from utils import db as _db
from utils.helpers import today_str, generate_id
import config

auth = Blueprint("auth", __name__)

SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.xlsx")
CLIENTS_FILE  = os.path.join(config.DATA_DIR, "clients.xlsx")
SETTINGS_HEADERS = ["key", "value"]
CLIENT_HEADERS = ["client_id", "name", "mobile", "email", "address", "username", "password", "status", "reg_date"]


def get_setting(key, default=""):
    # Prefer DB-backed settings when available
    try:
        if _db.is_enabled():
            return _db.get_setting(key, default)
    except Exception:
        pass

    rows = read_rows(SETTINGS_FILE)
    for r in rows:
        if r.get("key") == key:
            return r.get("value") or default
    return default


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN ROUTE (Admin & Client password-based login)
# ══════════════════════════════════════════════════════════════════════════════
@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard") if current_user.role == "admin"
                        else url_for("client.dashboard"))

    if request.method == "POST":
        role = request.form.get("role", "client")

        if role == "admin":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            stored_user = get_setting("admin_username", config.ADMIN_USERNAME)
            stored_hash = get_setting("admin_password_hash", "")

            if not stored_hash:
                stored_hash = generate_password_hash(config.ADMIN_DEFAULT_PASSWORD)

            if username.lower() == stored_user.lower() and check_password_hash(stored_hash, password):
                user = AdminUser()
                login_user(user)
                flash("Welcome back, Admin!", "success")
                return redirect(url_for("admin.dashboard"))
            else:
                flash("Invalid admin username or password.", "danger")

        else:  # Client login
            login_name = request.form.get("name", "").strip()
            password = request.form.get("password", "")

            if not login_name or not password:
                flash("Please enter your name and password.", "danger")
                return redirect(url_for("auth.login"))

            matched = None
            if _db.is_enabled():
                matched = _db.get_client_by_name(login_name)
            else:
                clients = read_rows(CLIENTS_FILE)
                for c in clients:
                    c_name = str(c.get("name", "")).strip().lower()
                    if login_name.lower() == c_name:
                        matched = c
                        break

            if matched:
                if str(matched.get("status", "Active")).lower() != "active":
                    flash("Your account is deactivated. Contact admin.", "warning")
                    return redirect(url_for("auth.login"))

                stored_hash = str(matched.get("password", ""))
                if stored_hash and check_password_hash(stored_hash, password):
                    user = ClientUser(matched)
                    login_user(user)
                    flash(f"Welcome, {matched.get('name')}!", "success")
                    return redirect(url_for("client.dashboard"))

                flash("Incorrect password.", "danger")
            else:
                flash("No client account found with that name.", "danger")

    return render_template("login.html")


# ══════════════════════════════════════════════════════════════════════════════
# CLIENT SIGN UP (Saves user details and hashed password)
# ══════════════════════════════════════════════════════════════════════════════
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard") if current_user.role == "admin"
                        else url_for("client.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        address = request.form.get("address", "").strip()

        if not name or not email or not mobile or not password:
            flash("All starred fields are required.", "danger")
            return redirect(url_for("auth.signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.signup"))

        clients = read_rows(CLIENTS_FILE)

        # Ensure single registration check: no duplicate email or mobile
        # Check duplicates (DB or Excel)
        if _db.is_enabled():
            # naive check via excel fallback list to keep behavior consistent
            for c in clients:
                if str(c.get("email", "")).strip().lower() == email:
                    flash("An account with this email already exists. Please log in.", "warning")
                    return redirect(url_for("auth.login"))
                if str(c.get("mobile", "")).strip() == mobile:
                    flash("An account with this mobile number already exists. Please log in.", "warning")
                    return redirect(url_for("auth.login"))
        else:
            for c in clients:
                if str(c.get("email", "")).strip().lower() == email:
                    flash("An account with this email already exists. Please log in.", "warning")
                    return redirect(url_for("auth.login"))

                if str(c.get("mobile", "")).strip() == mobile:
                    flash("An account with this mobile number already exists. Please log in.", "warning")
                    return redirect(url_for("auth.login"))

        # Generate new Client ID
        client_id = generate_id("C", clients, "client_id")
        username = "".join(ch for ch in name.lower() if ch.isalnum()) or "client"
        username = f"{username}_{client_id.lower()}"

        # Save client row with hashed password
        new_client = {
            "client_id": client_id,
            "name": name,
            "mobile": mobile,
            "email": email,
            "address": address,
            "username": username,
            "password": generate_password_hash(password),
            "status": "Active",
            "reg_date": today_str(),
        }

        if _db.is_enabled():
            _db.create_client(new_client)
            user = ClientUser(new_client)
            login_user(user)
        else:
            clients.append(new_client)
            write_rows(CLIENTS_FILE, clients, CLIENT_HEADERS)
            user = ClientUser(new_client)
            login_user(user)
        flash(f"Account created successfully! Welcome, {name}.", "success")
        return redirect(url_for("client.dashboard"))

    return render_template("signup.html")


# ══════════════════════════════════════════════════════════════════════════════
# LOGOUT
# ══════════════════════════════════════════════════════════════════════════════
@auth.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    response = redirect(url_for("auth.login"))
    response.delete_cookie("remember_token")
    return response


# ══════════════════════════════════════════════════════════════════════════════
# CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════════════════
@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow logged in user to change their password or email."""
    if request.method == "POST":
        old_pw = request.form.get("old_password", "")
        new_pw = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if new_pw != confirm:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("auth.change_password"))

        if len(new_pw) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.change_password"))

        hashed_pw = generate_password_hash(new_pw)
        if current_user.role == "admin":
            stored_hash = get_setting("admin_password_hash", "")
            if not check_password_hash(stored_hash, old_pw):
                flash("Current password incorrect.", "danger")
                return redirect(url_for("auth.change_password"))

            # Update password (DB and Excel)
            if _db.is_enabled():
                _db.set_setting("admin_password_hash", hashed_pw)
            
            rows = read_rows(SETTINGS_FILE)
            for r in rows:
                if r["key"] == "admin_password_hash":
                    r["value"] = hashed_pw
                    break
            write_rows(SETTINGS_FILE, rows, SETTINGS_HEADERS)

            flash("Admin password updated successfully.", "success")
            return redirect(url_for("admin.dashboard"))

        else:  # Client password update
            if _db.is_enabled():
                # Verify current password via DB
                client = _db.get_client_by_name(current_user.name)
                if not client or not check_password_hash(str(client.get("password", "")), old_pw):
                    flash("Current password incorrect.", "danger")
                    return redirect(url_for("auth.change_password"))
                _db.update_client_password(current_user.id, hashed_pw)
            else:
                clients = read_rows(CLIENTS_FILE)
                matched_client = next((c for c in clients if c.get("client_id") == current_user.id), None)
                if not matched_client or not check_password_hash(str(matched_client.get("password", "")), old_pw):
                    flash("Current password incorrect.", "danger")
                    return redirect(url_for("auth.change_password"))

            # Always write to Excel to keep local copy in sync
            clients = read_rows(CLIENTS_FILE)
            updated = False
            for c in clients:
                if c.get("client_id") == current_user.id:
                    c["password"] = hashed_pw
                    updated = True
                    break

            if updated:
                write_rows(CLIENTS_FILE, clients, CLIENT_HEADERS)
            
            flash("Your password has been updated.", "success")
            return redirect(url_for("client.dashboard"))

    return render_template("change_password.html")
