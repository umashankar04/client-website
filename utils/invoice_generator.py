"""
utils/invoice_generator.py
──────────────────────────
Generate a professional PDF invoice using ReportLab.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

import config


def generate_invoice(inv_data, output_path):
    """
    Build a PDF invoice file.

    inv_data dict keys:
        invoice_no, date, client_name, client_mobile, client_email,
        client_address, service_name, quantity, unit_price, total,
        amount_paid, balance, payment_status, payment_method, txn_id,
        footer_text
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    story = []   # List of flowable elements to put on the page

    # ── Custom paragraph styles ───────────────────────────────────────
    title_style = ParagraphStyle(
        "InvTitle", fontName="Helvetica-Bold", fontSize=22,
        textColor=colors.HexColor("#4f46e5"), alignment=TA_LEFT
    )
    sub_style = ParagraphStyle(
        "InvSub", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#6b7280"), alignment=TA_LEFT
    )
    label_style = ParagraphStyle(
        "InvLabel", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.HexColor("#374151")
    )
    value_style = ParagraphStyle(
        "InvValue", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#111827")
    )
    right_style = ParagraphStyle(
        "InvRight", fontName="Helvetica-Bold", fontSize=9,
        alignment=TA_RIGHT, textColor=colors.HexColor("#374151")
    )
    footer_style = ParagraphStyle(
        "InvFooter", fontName="Helvetica-Oblique", fontSize=8,
        textColor=colors.HexColor("#9ca3af"), alignment=TA_CENTER
    )
    total_style = ParagraphStyle(
        "InvTotal", fontName="Helvetica-Bold", fontSize=11,
        textColor=colors.HexColor("#ffffff"), alignment=TA_RIGHT
    )

    # ── Determine status color ─────────────────────────────────────────
    status = str(inv_data.get("payment_status", "Pending")).upper()
    if status == "PAID":
        status_color = colors.HexColor("#059669")
    elif "PARTIAL" in status:
        status_color = colors.HexColor("#d97706")
    else:
        status_color = colors.HexColor("#dc2626")

    # ── HEADER: Logo left, Invoice meta right ─────────────────────────
    logo_path = os.path.join(config.UPLOADS_DIR, "logo.png")
    if os.path.exists(logo_path):
        try:
            logo_cell = Image(logo_path, width=40*mm, height=16*mm)
        except Exception:
            logo_cell = Paragraph("<b>VEMS</b>", title_style)
    else:
        logo_cell = Paragraph("<b>VEMS</b>", title_style)

    header_data = [[
        logo_cell,
        Paragraph(
            f"<b>INVOICE #{inv_data.get('invoice_no')}</b><br/>"
            f"Date: {inv_data.get('date')}<br/>"
            f"Status: <font color='#{status_color.hexval()[2:]}'>■ {inv_data.get('payment_status')}</font>",
            right_style
        )
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 90*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6*mm))

    # Horizontal divider
    story.append(Table([[""]], colWidths=[180*mm],
                       style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb"))]))
    story.append(Spacer(1, 5*mm))

    # ── BILL TO / FROM ────────────────────────────────────────────────
    bill_to = (
        f"<b>Bill To:</b><br/>"
        f"{inv_data.get('client_name', '')}<br/>"
        f"📱 {inv_data.get('client_mobile', '')}<br/>"
        f"✉ {inv_data.get('client_email', '')}<br/>"
        f"{inv_data.get('client_address', '')}"
    )
    from_info = (
        "<b>From:</b><br/>"
        "Video Editing Studio<br/>"
        f"📱 {inv_data.get('contact_phone', config.DEFAULT_PHONE)}<br/>"
        f"Instagram: @pradhan04_"
    )
    addr_data = [[
        Paragraph(bill_to, value_style),
        Paragraph(from_info, value_style)
    ]]
    addr_table = Table(addr_data, colWidths=[90*mm, 90*mm])
    addr_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 6*mm))

    # ── SERVICE TABLE ─────────────────────────────────────────────────
    def white(text): return f"<font color='white'><b>{text}</b></font>"

    qty = inv_data.get("quantity", 1)
    unit_price = inv_data.get("unit_price", 0.0)
    total = inv_data.get("total", 0.0)

    items_data = [
        [
            Paragraph(white("Service Description"), label_style),
            Paragraph(white("Unit Price"), label_style),
            Paragraph(white("Qty"), label_style),
            Paragraph(white("Total"), label_style),
        ],
        [
            Paragraph(str(inv_data.get("service_name", "")), value_style),
            Paragraph(f"₹{float(unit_price):.2f}", value_style),
            Paragraph(str(qty), value_style),
            Paragraph(f"₹{float(total):.2f}", value_style),
        ]
    ]
    items_table = Table(items_data, colWidths=[90*mm, 35*mm, 20*mm, 35*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # ── SUMMARY: Subtotal / Paid / Balance ────────────────────────────
    amount_paid = float(inv_data.get("amount_paid", 0.0))
    balance = float(inv_data.get("balance", 0.0))

    summary_data = [
        ["", Paragraph("<b>Subtotal:</b>", label_style),   Paragraph(f"₹{float(total):.2f}", value_style)],
        ["", Paragraph("<b>Amount Paid:</b>", label_style), Paragraph(f"₹{amount_paid:.2f}", value_style)],
        ["", Paragraph("<b>Balance Due:</b>", label_style), Paragraph(f"₹{balance:.2f}", value_style)],
    ]
    summary_table = Table(summary_data, colWidths=[90*mm, 55*mm, 35*mm])
    summary_table.setStyle(TableStyle([
        ("LINEBELOW", (1, 1), (2, 1), 0.5, colors.HexColor("#e5e7eb")),
        ("LINEBELOW", (1, 2), (2, 2), 1.5, colors.HexColor("#4f46e5")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6*mm))

    # ── PAYMENT INFO + QR CODE ────────────────────────────────────────
    pay_text = (
        "<b>Payment Information:</b><br/>"
        f"Method: {inv_data.get('payment_method', 'N/A')}<br/>"
        f"Transaction ID: {inv_data.get('txn_id', 'N/A')}<br/><br/>"
        "Scan QR to pay via UPI (GPay / PhonePe / Paytm)"
    )

    qr_path = os.path.join(config.UPLOADS_DIR, "qr.png")
    if os.path.exists(qr_path):
        try:
            qr_cell = Image(qr_path, width=28*mm, height=28*mm)
        except Exception:
            qr_cell = Paragraph("[QR]", value_style)
    else:
        qr_cell = Paragraph("[No QR Uploaded]", value_style)

    pay_data = [[
        Paragraph(pay_text, value_style),
        Paragraph("<b>Pay Here:</b>", label_style),
        qr_cell
    ]]
    pay_table = Table(pay_data, colWidths=[100*mm, 30*mm, 50*mm])
    pay_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(pay_table)
    story.append(Spacer(1, 8*mm))

    # ── FOOTER ────────────────────────────────────────────────────────
    footer_text = inv_data.get("footer_text", config.DEFAULT_FOOTER)
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    return True
