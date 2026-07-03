import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_invoice_pdf(invoice_data, output_path, logo_path=None, qr_code_path=None, contact_info=None, footer_text=None):
    """
    Generates a professional PDF invoice using ReportLab.
    invoice_data is a dictionary containing:
      - invoice_no
      - client_name
      - client_mobile
      - client_email
      - client_address
      - date
      - service_name
      - quantity
      - price
      - total
      - payment_status
      - amount_paid
      - remaining_balance
      - payment_method
      - transaction_id
    """
    # Ensure directory exists
    dir_name = os.path.dirname(output_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # Document setup (Letter size, 0.5 inch margins for max printable area)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    
    # Styles Setup
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e293b')
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    
    meta_right_style = ParagraphStyle(
        'MetaRightText',
        parent=meta_style,
        alignment=2 # Right align
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )

    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )
    
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )
    
    cell_right = ParagraphStyle(
        'CellRightText',
        parent=cell_style,
        alignment=2
    )

    cell_right_bold = ParagraphStyle(
        'CellRightBoldText',
        parent=cell_bold,
        alignment=2
    )

    # Set status badge color
    status = invoice_data.get('payment_status', 'Pending').upper()
    if status == 'PAID':
        status_color = '#059669' # Green
    elif status == 'PARTIAL PAYMENT' or status == 'PARTIAL':
        status_color = '#d97706' # Orange
    else:
        status_color = '#dc2626' # Red

    # Header Row (Logo / Brand Name on Left, INVOICE label and Metadata on Right)
    logo_flowable = None
    if logo_path and os.path.exists(logo_path):
        try:
            # Scale logo to max width 150, max height 60
            logo_flowable = Image(logo_path, width=1.5*inch, height=0.6*inch)
        except Exception:
            logo_flowable = Paragraph("<b>COMPANY LOGO</b>", title_style)
    else:
        logo_flowable = Paragraph("<b>VEMS SYSTEM</b>", title_style)

    header_right_content = f"""
    <b>INVOICE</b><br/>
    Invoice No: #{invoice_data.get('invoice_no')}<br/>
    Date: {invoice_data.get('date')}<br/>
    Status: <font color="{status_color}"><b>{status}</b></font>
    """
    
    header_table_data = [
        [logo_flowable, Paragraph(header_right_content, meta_right_style)]
    ]
    
    # 540pt is printable width on letter with 36pt margins
    header_table = Table(header_table_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # Client Info & Company Info
    contact_phone = contact_info.get('phone', '9668797558') if contact_info else '9668797558'
    contact_insta = contact_info.get('instagram', 'https://www.instagram.com/pradhan04_') if contact_info else 'https://www.instagram.com/pradhan04_'
    
    company_info_text = f"""
    <b>Video Editing Mgmt System</b><br/>
    WhatsApp/Call: {contact_phone}<br/>
    Instagram: {contact_insta.split('/')[-1]}<br/>
    Email: support@vems.com
    """
    
    client_info_text = f"""
    <b>Bill To:</b><br/>
    <b>Name:</b> {invoice_data.get('client_name')}<br/>
    <b>Email:</b> {invoice_data.get('client_email', 'N/A')}<br/>
    <b>Mobile:</b> {invoice_data.get('client_mobile')}<br/>
    <b>Address:</b> {invoice_data.get('client_address', 'N/A')}
    """
    
    info_table_data = [
        [Paragraph(client_info_text, cell_style), Paragraph(company_info_text, cell_style)]
    ]
    
    info_table = Table(info_table_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Items Table
    story.append(Paragraph("Service Details", section_heading))
    
    # Table Headers
    items_data = [
        [
            Paragraph("<b>Service Description</b>", cell_bold),
            Paragraph("<b>Price (₹)</b>", cell_right_bold),
            Paragraph("<b>Qty</b>", cell_right_bold),
            Paragraph("<b>Total (₹)</b>", cell_right_bold)
        ]
    ]
    
    # Item row
    items_data.append([
        Paragraph(invoice_data.get('service_name', 'Video Service'), cell_style),
        Paragraph(f"₹{invoice_data.get('price', 0.0):.2f}", cell_right),
        Paragraph(str(invoice_data.get('quantity', 1)), cell_right),
        Paragraph(f"₹{invoice_data.get('total', 0.0):.2f}", cell_right_bold)
    ])
    
    items_table = Table(items_data, colWidths=[240, 100, 80, 120])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    # Quick fix: reportlab TextColors inside Paragraph are handled by styling, but standard plain text handles table textcolor. Let's make headers white in the paragraphs.
    items_data[0] = [
        Paragraph("<font color='white'><b>Service Description</b></font>", cell_bold),
        Paragraph("<font color='white'><b>Price (₹)</b></font>", cell_right_bold),
        Paragraph("<font color='white'><b>Qty</b></font>", cell_right_bold),
        Paragraph("<font color='white'><b>Total (₹)</b></font>", cell_right_bold)
    ]
    items_table = Table(items_data, colWidths=[240, 100, 80, 120])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 15))
    
    # Financial breakdown (Subtotal, Paid, Balance)
    amount_paid = float(invoice_data.get('amount_paid', 0.0))
    rem_balance = float(invoice_data.get('remaining_balance', 0.0))
    
    summary_data = [
        [Paragraph("", cell_style), Paragraph("<b>Subtotal:</b>", cell_right), Paragraph(f"₹{invoice_data.get('total', 0.0):.2f}", cell_right)],
        [Paragraph("", cell_style), Paragraph("<b>Amount Paid:</b>", cell_right), Paragraph(f"₹{amount_paid:.2f}", cell_right)],
        [Paragraph("", cell_style), Paragraph("<b>Remaining Balance:</b>", cell_right_bold), Paragraph(f"₹{rem_balance:.2f}", cell_right_bold)]
    ]
    
    summary_table = Table(summary_data, colWidths=[240, 180, 120])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (1,0), (2,0), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (1,1), (2,1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (1,2), (2,2), 1.5, colors.HexColor('#334155')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Payment Method Details & QR Code Side-by-Side
    payment_info_cell = []
    payment_info_cell.append(Paragraph("<b>Payment Details:</b>", cell_bold))
    if invoice_data.get('payment_method') and invoice_data.get('payment_method') != 'N/A':
        payment_info_cell.append(Paragraph(f"Method: {invoice_data.get('payment_method')}", cell_style))
    if invoice_data.get('transaction_id') and invoice_data.get('transaction_id') != 'N/A':
        payment_info_cell.append(Paragraph(f"Transaction ID: {invoice_data.get('transaction_id')}", cell_style))
    payment_info_cell.append(Paragraph("Scan QR code to pay using UPI apps (GPay, PhonePe, Paytm).", cell_style))
    
    # Render QR Code Image
    qr_flowable = None
    if qr_code_path and os.path.exists(qr_code_path):
        try:
            # QR code is square, let's make it 1.2 x 1.2 inches
            qr_flowable = Image(qr_code_path, width=1.2*inch, height=1.2*inch)
        except Exception:
            qr_flowable = Paragraph("[QR Code Image]", cell_style)
    else:
        qr_flowable = Paragraph("[No QR Uploaded]", cell_style)
        
    payment_table_data = [
        [payment_info_cell, Paragraph("<b>Pay Here:</b>", cell_bold), qr_flowable]
    ]
    
    payment_table = Table(payment_table_data, colWidths=[320, 100, 120])
    payment_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 25))
    
    # Footer Section
    final_footer_text = footer_text or "Thank you for working with us! For query, call 9668797558."
    footer_style = ParagraphStyle(
        'InvoiceFooter',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        alignment=1, # Centered
        textColor=colors.HexColor('#64748b')
    )
    
    story.append(Paragraph(final_footer_text, footer_style))
    
    # Build Document
    doc.build(story)
    return True


def generate_report_pdf(report_type, start_date, end_date, summary_data, records, output_path):
    """
    Generates a clean PDF summary report of work entries and earnings.
    """
    dir_name = os.path.dirname(output_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Typography Styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=15
    )

    section_style = ParagraphStyle(
        'ReportSection',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    cell_style = ParagraphStyle(
        'ReportCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )
    
    cell_bold = ParagraphStyle(
        'ReportCellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )
    
    cell_right = ParagraphStyle(
        'ReportCellRight',
        parent=cell_style,
        alignment=2
    )

    cell_right_bold = ParagraphStyle(
        'ReportCellRightBold',
        parent=cell_bold,
        alignment=2
    )

    story.append(Paragraph(f"{report_type} Earnings & Activity Report", title_style))
    story.append(Paragraph(f"Period: {start_date} to {end_date} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    
    # Summary Dashboard Table
    story.append(Paragraph("Financial Summary", section_style))
    
    sum_data = [
        [
            Paragraph("<font color='white'><b>Metric</b></font>", cell_bold), 
            Paragraph("<font color='white'><b>Value</b></font>", cell_right_bold)
        ],
        [Paragraph("Total Projects / Entries", cell_style), Paragraph(str(summary_data.get('total_projects', 0)), cell_right)],
        [Paragraph("Gross Earnings (Total Invoiced)", cell_style), Paragraph(f"₹{summary_data.get('total_earnings', 0.0):.2f}", cell_right)],
        [Paragraph("Payments Received (Paid)", cell_style), Paragraph(f"₹{summary_data.get('total_paid', 0.0):.2f}", cell_right)],
        [Paragraph("Outstanding Receivables (Pending)", cell_style), Paragraph(f"₹{summary_data.get('total_pending', 0.0):.2f}", cell_right)]
    ]
    
    sum_table = Table(sum_data, colWidths=[270, 270])
    sum_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 15))
    
    # Detailed Entries Table
    story.append(Paragraph("Detailed Work Entries", section_style))
    
    headers = [
        Paragraph("<font color='white'><b>Date</b></font>", cell_bold),
        Paragraph("<font color='white'><b>Serial #</b></font>", cell_bold),
        Paragraph("<font color='white'><b>Client</b></font>", cell_bold),
        Paragraph("<font color='white'><b>Service Type</b></font>", cell_bold),
        Paragraph("<font color='white'><b>Qty</b></font>", cell_right_bold),
        Paragraph("<font color='white'><b>Total (₹)</b></font>", cell_right_bold),
        Paragraph("<font color='white'><b>Status</b></font>", cell_bold)
    ]
    
    table_data = [headers]
    
    for r in records:
        table_data.append([
            Paragraph(r.get('Date', ''), cell_style),
            Paragraph(r.get('Serial Number', ''), cell_style),
            Paragraph(r.get('Client Name', ''), cell_style),
            Paragraph(r.get('Service Type', ''), cell_style),
            Paragraph(str(r.get('Quantity', 0)), cell_right),
            Paragraph(f"₹{float(r.get('Total', 0.0)):.2f}", cell_right),
            Paragraph(r.get('Status', 'Pending'), cell_bold)
        ])
        
    # Widths sum up to 540pt
    col_widths = [65, 55, 110, 110, 35, 80, 85]
    records_table = Table(table_data, colWidths=col_widths)
    records_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(records_table)
    
    doc.build(story)
    return True
