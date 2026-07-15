from typing import List
import imaplib
import email
import os
from stripe_module import settings
from fpdf import FPDF
import re

def create_email_pdf(subject, body, filename, partner_tag=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Encode/Decode to handle latin-1 characters (common in Swedish)
    def clean(text):
        return text.encode('latin-1', 'replace').decode('latin-1')
    
    # Check if this is an Uber email - format it specially
    if partner_tag == "ubereats" or "uber" in subject.lower():
        # === UBER EATS STYLE FORMAT ===
        
        # Header: UBER EATS
        pdf.set_font("Arial", "B", 18)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(30, 10, "UBER", ln=False)
        pdf.set_font("Arial", "", 18)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, "EATS", ln=True)
        pdf.ln(8)
        
        # Restaurant name
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Ichiban Sushi", ln=True)
        
        # Extract date range from subject
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{2,4})', subject)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(80, 80, 80)
        if date_match:
            pdf.cell(0, 8, f"Betalningsöversikt över {date_match.group(1)} - {date_match.group(2)}", ln=True)
        pdf.ln(3)
        
        # Greeting
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "Hej Ichiban Sushi,", ln=True)
        pdf.ln(2)
        pdf.multi_cell(0, 5, clean("Vi hoppas att du har en bra vecka. Nedan hittar du din veckovisa betalningsöversikt. Fakturan för ovan nämnda period finns redan tillgänglig i Uber Eats Manager."))
        pdf.ln(2)
        pdf.cell(0, 5, "Tack för att du är en partner,", ln=True)
        pdf.cell(0, 5, "Uber Eats-teamet", ln=True)
        pdf.ln(8)
        
        # === Total försäljning section ===
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Total försäljning", ln=True)
        pdf.ln(3)
        
        # Extract values from body - convert Swedish format to simple format
        def convert_to_simple(swedish_amount):
            """Convert Swedish format (1 234,56) to simple format (1234.56)"""
            if not swedish_amount:
                return "0.00"
            # Remove spaces (thousand separator), replace comma with dot
            simple = swedish_amount.replace(" ", "").replace(",", ".")
            return simple
        
        # Extract all key values from the email body
        # Note: HTML-to-text conversion adds extra spaces, so use \s+ to match multiple spaces
        total_betalning_match = re.search(r'Total\s+Betalning\s+(-?[0-9.,]+)\s*kr', body, re.IGNORECASE)
        totalbelopp_match = re.search(r'Totalbelopp\s+\d*\s*([0-9.,]+)\s*kr', body, re.IGNORECASE)
        uber_fee_match = re.search(r'Uber\s+Eats-avgift\s+(-?[0-9.,]+)\s*kr', body, re.IGNORECASE)
        moms_match = re.search(r'Moms\s+på\s+Uber\s+Eats-avgift\s+(-?[0-9.,]+)\s*kr', body, re.IGNORECASE)
        netto_match = re.search(r'Nettoförsäljning\s+([0-9.,]+)\s*kr', body, re.IGNORECASE)
        orders_match = re.search(r'Beställningar\s+(\d+)', body, re.IGNORECASE)
        
        total_amount = convert_to_simple(total_betalning_match.group(1)) if total_betalning_match else "0.00"
        totalbelopp = convert_to_simple(totalbelopp_match.group(1)) if totalbelopp_match else None
        uber_fee = convert_to_simple(uber_fee_match.group(1)) if uber_fee_match else None
        moms = convert_to_simple(moms_match.group(1)) if moms_match else None
        netto = convert_to_simple(netto_match.group(1)) if netto_match else None
        num_orders = orders_match.group(1) if orders_match else "0"
        
        # Draw boxes for Beställningar and Total Betalning
        y_start = pdf.get_y()
        
        # Box 1: Beställningar
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(10, y_start, 90, 30)
        pdf.set_xy(10, y_start + 3)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(90, 5, "Beställningar", align='C', ln=True)
        pdf.set_xy(10, y_start + 12)
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(90, 12, num_orders, align='C')
        
        # Box 2: Total Betalning
        pdf.rect(105, y_start, 95, 30)
        pdf.set_xy(105, y_start + 3)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(95, 5, "Total Betalning", align='C', ln=True)
        pdf.set_xy(105, y_start + 12)
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(6, 149, 55)  # Uber green
        pdf.cell(95, 12, f"{total_amount} kr", align='C')
        
        pdf.set_y(y_start + 38)
        
        # === Betalningsberäkning section ===
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Betalningsberäkning", ln=True)
        pdf.ln(3)
        
        # Table header
        pdf.set_font("Arial", "B", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(60, 6, "DAG/UPPHÄMTNINGSTID", ln=False)
        pdf.cell(40, 6, "Beställningar", align='C', ln=False)
        pdf.cell(0, 6, "FÖRSÄLJNING (EFTER SKATT)", align='R', ln=True)
        pdf.ln(2)
        
        # Parse daily data from body
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(0, 0, 0)
        
        # Find all date-order-amount patterns
        lines = body.split('\n')
        for line in lines:
            # Match patterns like "12/17/25 3 881,00 kr" or "11/24/25 1 174,00 kr"
            day_match = re.match(r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d+)\s+([0-9.,]+)\s*kr', line.strip())
            if day_match:
                simple_amount = convert_to_simple(day_match.group(3))
                pdf.cell(60, 6, day_match.group(1), ln=False)
                pdf.cell(40, 6, day_match.group(2), align='C', ln=False)
                pdf.cell(0, 6, f"{simple_amount} kr", align='R', ln=True)
        
        pdf.ln(3)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        
        # Summary lines
        def add_summary_line(label, value, bold=False):
            if bold:
                pdf.set_font("Arial", "B", 10)
            else:
                pdf.set_font("Arial", "", 9)
            pdf.cell(100, 6, "", ln=False)
            pdf.cell(50, 6, label, ln=False)
            pdf.cell(0, 6, value, align='R', ln=True)
        
        # Display summary values (already extracted above)
        if totalbelopp:
            add_summary_line("Totalbelopp", f"{totalbelopp} kr")
        if uber_fee:
            add_summary_line("Uber Eats-avgift", f"{uber_fee} kr")
        if moms:
            add_summary_line("Moms på Uber Eats-avgift", f"{moms} kr")
        if netto:
            add_summary_line("Nettoförsäljning", f"{netto} kr")
        
        pdf.ln(5)
        
        # Final Total Betalning in green
        pdf.set_font("Arial", "B", 12)
        pdf.cell(100, 10, "", ln=False)
        pdf.set_text_color(6, 149, 55)
        pdf.cell(50, 10, "Total Betalning", ln=False)
        pdf.cell(0, 10, f"{total_amount} kr", align='R', ln=True)
        
    else:
        # DEFAULT FORMAT for other partners
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, clean(f"Subject: {subject}"), ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, clean(body))
    
    pdf.output(filename)
    return filename

def get_email_body(msg):
    """Extract plain text body from email."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode(errors='ignore')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(errors='ignore')
    return body

def get_html_body(msg):
    """Extract HTML body from email and convert to plain text."""
    html = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(errors='ignore')
                    break
    else:
        if msg.get_content_type() == 'text/html':
            payload = msg.get_payload(decode=True)
            if payload:
                html = payload.decode(errors='ignore')
    
    # Strip HTML tags and clean up
    if html:
        # Remove script/style tags and their content
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Replace <br> and </p> with newlines
        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</tr>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</td>', '  ', html, flags=re.IGNORECASE)
        # Remove all remaining HTML tags
        html = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        html = re.sub(r'\n\s*\n', '\n\n', html)
        html = html.strip()
    return html

def fetch_email_invoices(year: int, month: int) -> List[str]:
    """
    Connects to Gmail and downloads Wolt, Foodora, and Uber Eats payout reports/invoices.
    """
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        print("Email credentials not set in .env. Skipping email fetch.")
        return []

    downloaded_files = []
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)

    try:
        print(f"Connecting to {settings.EMAIL_HOST} for {settings.EMAIL_USER}...")
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        mail.select("inbox")

        import datetime
        
        # FIXED: Use strict month boundaries for email RECEIVED date (when money arrived)
        # This matches accounting principle: income recorded when payment hits bank account
        # NOT when work was performed (invoice period dates in subject lines)
        month_start = datetime.date(year, month, 1)
        if month == 12:
            month_end = datetime.date(year + 1, 1, 1)
        else:
            month_end = datetime.date(year, month + 1, 1)

        since_str  = month_start.strftime("%d-%b-%Y")
        before_str = month_end.strftime("%d-%b-%Y")

        date_criteria = f'(SINCE "{since_str}" BEFORE "{before_str}")'
        print(f"[FIXED] Fetching emails RECEIVED between {since_str} and {before_str} (payout month: {year}-{month:02d})")

        processed_ids = set()
        # FIXED: Search by partner and email received date only
        # Removed all work period date filtering from subjects
        queries = [
            (f'(SUBJECT "Wolt payout report" {date_criteria})', "wolt"),
            (f'(SUBJECT "underlag" SUBJECT "Foodora" {date_criteria})', "foodora"),
            (f'(FROM "restaurants.sweden@uber.com" {date_criteria})', "ubereats"),
        ]

        for full_query, default_tag in queries:
            result, data = mail.search(None, full_query)
            if result == "OK":
                for num in data[0].split():
                    # Deduplicate
                    if num in processed_ids: continue
                    processed_ids.add(num)
                    
                    result, data = mail.fetch(num, "(RFC822)")
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    subject = msg.get("Subject", "").lower()
                    
                    # Fine-tune tag based on subject
                    partner_tag = default_tag
                    if "wolt" in subject: partner_tag = "wolt"
                    elif "foodora" in subject: partner_tag = "foodora"
                    elif "uber" in subject: partner_tag = "ubereats"
                
                    found_pdf = False
                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue
                        if part.get("Content-Disposition") is None:
                            continue

                        filename = part.get_filename()
                        if filename and filename.lower().endswith(".pdf"):
                            # For Wolt: Only download the payout_report PDF (actual payout amount)
                            # Skip the main invoice (fee invoice) and sales_report
                            if partner_tag == "wolt":
                                # Only keep payout_report - it has "Belopp utbetalning" (actual payout)
                                if "sales_report" in filename.lower():
                                    print(f"Skipping Wolt sales report: {filename}")
                                    continue
                                
                                # For the main invoice (Ichiban_Sushi_YYYY-MM-DD_...), skip it
                                # Main invoice filename has date pattern but no report type keyword
                                is_payout_report = "payout_report" in filename.lower()
                                is_main_invoice = not is_payout_report and re.search(r'\d{4}-\d{2}-\d{2}', filename)
                                
                                if is_main_invoice:
                                    print(f"Skipping Wolt main fee invoice: {filename}")
                                    continue
                                
                                # FIXED: Removed work period date filter from filename
                                # Keep ALL payout_reports received in target month, regardless of period dates
                                print(f"Keeping Wolt payout report (received in {year}-{month:02d}): {filename}")
                            
                            # Prepend partner tag so reconciliation finds it
                            # Sanitize filename: remove newlines, carriage returns, and extra spaces
                            clean_filename = filename.replace('\n', '').replace('\r', '').replace('  ', ' ').strip()
                            safe_filename = f"{partner_tag}_{num.decode()}_{clean_filename}"
                            filepath = os.path.join(settings.INVOICE_STORAGE_PATH, safe_filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            
                            print(f"Downloaded attachment from {partner_tag}: {safe_filename}")
                            downloaded_files.append(os.path.abspath(filepath))
                            found_pdf = True
                    
                    # Fallback: Create PDF from body if no attachment found
                    # ONLY for Uber Eats (which sends HTML payment summaries)
                    # Skip for Foodora/Wolt (they always have PDF attachments for real invoices)
                    if not found_pdf and partner_tag == "ubereats":
                        # FIXED: Removed work period date filter from Uber subject
                        # Keep ALL Uber emails received in target month, regardless of period dates
                        print(f"No PDF found for {partner_tag} (Subject: {subject}). Generating from email body...")
                        
                        # Try HTML first (Uber sends HTML emails)
                        body_text = get_html_body(msg)
                        if not body_text.strip():
                            # Fallback to plain text
                            body_text = get_email_body(msg)
                        
                        if body_text.strip():
                            safe_filename = f"{partner_tag}_{num.decode()}_email_body.pdf"
                            filepath = os.path.join(settings.INVOICE_STORAGE_PATH, safe_filename)
                            create_email_pdf(subject, body_text, filepath, partner_tag)
                            downloaded_files.append(os.path.abspath(filepath))
                            print(f"Generated PDF from email body: {safe_filename}")
                    elif not found_pdf:
                        print(f"Skipping {partner_tag} email without PDF attachment (likely promotional): {subject[:50]}")

        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Error fetching emails: {e}")

    return downloaded_files
