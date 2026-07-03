"""
utils/email_sender.py
─────────────────────
Send OTP emails via Gmail SMTP (or any SMTP provider).

HOW TO CONFIGURE GMAIL:
  1. Go to your Gmail → Settings → Security → 2-Step Verification → ON
  2. Then go to: https://myaccount.google.com/apppasswords
  3. Create an App Password for "Mail" → copy the 16-char password
  4. Set SMTP_EMAIL and SMTP_PASSWORD in Settings page inside VEMS

The credentials are stored in settings.xlsx and loaded at runtime.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config
from utils.excel_manager import read_rows


def _get_smtp_settings():
    """Load SMTP credentials from settings.xlsx."""
    settings_path = os.path.join(config.DATA_DIR, "settings.xlsx")
    rows = read_rows(settings_path)
    settings = {r["key"]: r.get("value", "") for r in rows}
    return {
        "smtp_host":     settings.get("smtp_host",     "smtp.gmail.com"),
        "smtp_port":     int(settings.get("smtp_port", 587)),
        "smtp_email":    settings.get("smtp_email",    ""),
        "smtp_password": settings.get("smtp_password", ""),
        "smtp_name":     settings.get("smtp_name",     "VEMS"),
    }


def send_otp_email(to_email: str, otp: str, recipient_name: str = "") -> tuple[bool, str]:
    """
    Send a 6-digit OTP to the given email address.

    Returns:
        (True, "")           on success
        (False, error_msg)   on failure
    """
    cfg = _get_smtp_settings()

    if not cfg["smtp_email"] or not cfg["smtp_password"]:
        return False, "Email not configured. Please set SMTP credentials in Settings."

    # Build a nice HTML email
    name_display = recipient_name if recipient_name else "User"
    html_body = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:480px;margin:auto;
                background:#1c1f35;border-radius:16px;overflow:hidden;color:#e2e4f0">
      <div style="background:linear-gradient(135deg,#6c63ff,#a855f7);padding:28px 32px;text-align:center">
        <div style="font-size:36px">🎬</div>
        <h1 style="color:#fff;font-size:22px;margin:8px 0 0">VEMS Login OTP</h1>
        <p style="color:rgba(255,255,255,0.75);font-size:13px;margin:4px 0 0">
          Video Editing Management System
        </p>
      </div>
      <div style="padding:32px">
        <p style="margin:0 0 8px;font-size:15px">Hello, <b>{name_display}</b> 👋</p>
        <p style="color:#9299b8;font-size:13px;margin:0 0 24px">
          Use the OTP below to log into your VEMS account.
          This code is valid for <b>10 minutes</b> and can only be used once.
        </p>

        <!-- OTP Box -->
        <div style="background:#141728;border:1px solid rgba(108,99,255,0.3);
                    border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
          <p style="color:#9299b8;font-size:12px;margin:0 0 8px;
                    text-transform:uppercase;letter-spacing:1px">Your One-Time Password</p>
          <div style="font-size:40px;font-weight:800;letter-spacing:10px;
                      color:#6c63ff;font-family:monospace">{otp}</div>
        </div>

        <p style="color:#f87171;font-size:12px;margin:0">
          ⚠️ Never share this OTP with anyone. If you did not request this, ignore this email.
        </p>
      </div>
      <div style="background:#141728;padding:16px 32px;text-align:center;
                  border-top:1px solid rgba(255,255,255,0.06)">
        <p style="color:#7880a0;font-size:11px;margin:0">
          &copy; VEMS · Video Editing Management System ·
          <a href="https://instagram.com/pradhan04_" style="color:#6c63ff">@pradhan04_</a>
        </p>
      </div>
    </div>
    """

    plain_body = f"Your VEMS OTP is: {otp}\nValid for 10 minutes. Do not share it."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[VEMS] Your Login OTP: {otp}"
        msg["From"]    = f"{cfg['smtp_name']} <{cfg['smtp_email']}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body,  "html"))

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["smtp_email"], cfg["smtp_password"])
            server.sendmail(cfg["smtp_email"], [to_email], msg.as_string())

        return True, ""

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Check your App Password in Settings."
    except smtplib.SMTPException as e:
        return False, f"Email send failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
