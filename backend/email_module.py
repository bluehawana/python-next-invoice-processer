from typing import List
import imaplib
import email
import email.utils
import email.header
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

def payment_window(year: int, month: int):
    """[start, end) dates of the invoices belonging to a payment month:
    15th of the previous month (its last two weeks) up to the 1st of the next month."""
    import datetime
    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    start = datetime.date(prev_year, prev_month, 15)
    end = datetime.date(year + 1, 1, 1) if month == 12 else datetime.date(year, month + 1, 1)
    return start, end


def _received_index_path() -> str:
    return os.path.join(settings.INVOICE_STORAGE_PATH, "_received_index.json")


def load_received_index() -> dict:
    """filename -> ISO date the invoice email was received."""
    import json
    try:
        with open(_received_index_path()) as f:
            return json.load(f)
    except Exception:
        return {}


def save_received_index(index: dict):
    import json
    try:
        with open(_received_index_path(), "w") as f:
            json.dump(index, f, indent=1, sort_keys=True)
    except Exception as e:
        print(f"Could not save received-date index: {e}")


MONTH_NAMES_EN = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"]
MONTH_TAGS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def create_uber_summary_pdf(subject: str, body: str, net_payout: str, filepath: str):
    """Printable copy of a weekly Uber Eats payout summary mail (plain, nothing invented)."""
    def clean(text):
        return text.replace("\u2212", "-").encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Uber Eats - Ichiban Sushi", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, clean(subject))
    pdf.ln(3)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, clean(f"Nettoutbetalning {net_payout} kr"), ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", "", 9)
    # break the flattened mail text back into readable lines at each amount
    text = re.sub(r'\s+', ' ', body)
    text = text.split("Ett enkelt sätt att visa")[0]
    text = re.sub(r'(\d,\d{2} kr)\s*', r'\1\n', text)
    for line in text.split("\n"):
        if line.strip():
            pdf.multi_cell(0, 5, clean(line.strip()))
    pdf.output(filepath)


def _fetch_uber_invoices(mail, year: int, month: int, window_start, window_end, received_index: dict) -> List[str]:
    """
    Uber Eats invoices for a payment month, straight from the mailbox:
    1. the official monthly statement PDF (monthly_statement_<Month>_<Year>.pdf) when it exists -
       it lists every payout received during the month;
    2. otherwise the weekly payout summary mails received in the payment window.
    """
    import datetime
    files: List[str] = []
    tag = f"{MONTH_TAGS[month - 1]}{year}"
    statement_name = f"monthly_statement_{MONTH_NAMES_EN[month - 1]}_{year}.pdf".lower()
    late_end = window_end + datetime.timedelta(days=20)
    criteria = (f'(FROM "uber.com" SINCE "{window_start.strftime("%d-%b-%Y")}" '
                f'BEFORE "{late_end.strftime("%d-%b-%Y")}")')
    result, data = mail.search(None, criteria)
    if result != "OK":
        return files

    statement_path = None
    weekly = []   # (received_date, subject, body, net_payout, num)
    for num in data[0].split():
        result, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        try:
            received = email.utils.parsedate_to_datetime(msg.get("Date")).date()
        except Exception:
            continue
        subject = " ".join(str(email.header.make_header(email.header.decode_header(msg.get("Subject", "")))).split())

        for part in msg.walk():
            fname = (part.get_filename() or "").lower()
            if fname == statement_name:
                statement_path = os.path.abspath(os.path.join(settings.INVOICE_STORAGE_PATH, f"ubereats_{tag}_statement.pdf"))
                with open(statement_path, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"Downloaded Uber monthly statement: {os.path.basename(statement_path)}")

        if "utbetalningssammanfattning" in subject.lower() and window_start <= received < window_end:
            body = get_html_body(msg) or get_email_body(msg)
            m = re.search(r'Nettoutbetalning\s*([\d\s\xa0]+,\d{2})\s*kr', body)
            if m:
                weekly.append((received, subject, body, " ".join(m.group(1).split()), num.decode()))

    if statement_path:
        # the statement already contains every payout of the month
        return [statement_path]

    for received, subject, body, net, num in weekly:
        name = f"ubereats_{num}_payout_summary_{received.isoformat()}.pdf"
        path = os.path.abspath(os.path.join(settings.INVOICE_STORAGE_PATH, name))
        create_uber_summary_pdf(subject, body, net, path)
        received_index[name] = received.isoformat()
        files.append(path)
        print(f"Generated Uber weekly payout summary: {name} ({net} kr)")
    return files


def _ework_mailboxes() -> list:
    """Mailboxes searched for Ework self-billing invoices: the invoice mailbox (also catches mails
    forwarded to it) and, when configured, the mailbox Ework sends them to
    (EWORK_EMAIL_USER / EWORK_EMAIL_PASS in .env, a Gmail app password)."""
    boxes = [(settings.EMAIL_HOST, settings.EMAIL_USER, settings.EMAIL_PASS)]
    user, pwd = os.getenv("EWORK_EMAIL_USER"), os.getenv("EWORK_EMAIL_PASS")
    if user and pwd and user != settings.EMAIL_USER:
        boxes.append((os.getenv("EWORK_EMAIL_HOST") or "imap.gmail.com", user, pwd))
    return boxes


def _fetch_ework_invoices(year: int, month: int, window_start, window_end) -> List[str]:
    """
    Ework Group "New Self Billing invoice SBIGAB... from Ework Group AB" mails (direct or forwarded),
    PDF attached. They are matched to the sheet by amount, so the search window is generous.
    """
    import datetime
    files: List[str] = []
    tag = f"{MONTH_TAGS[month - 1]}{year}"
    late_end = window_end + datetime.timedelta(days=20)
    seen = set()
    for host, user, pwd in _ework_mailboxes():
        try:
            mail = imaplib.IMAP4_SSL(host)
            mail.login(user, pwd)
            # search every folder (forwarded/archived mails are not in the inbox)
            folder = "inbox"
            for line in mail.list()[1]:
                decoded = line.decode()
                if "\\All" in decoded:
                    folder = decoded.split(' "/" ')[-1]
            mail.select(folder, readonly=True)
            query = (f'"Self Billing invoice" ework has:attachment '
                     f'after:{window_start.strftime("%Y/%m/%d")} before:{late_end.strftime("%Y/%m/%d")}')
            result, data = mail.search(None, "X-GM-RAW", f'"{query.replace(chr(34), chr(92) + chr(34))}"')
            if result != "OK":
                result, data = mail.search(None, f'(SUBJECT "Self Billing invoice" SINCE "{window_start.strftime("%d-%b-%Y")}")')
            for num in data[0].split():
                result, msg_data = mail.fetch(num, "(BODY.PEEK[])")
                msg = email.message_from_bytes(msg_data[0][1])
                for part in msg.walk():
                    fname = os.path.basename(part.get_filename() or "")
                    if not fname.lower().endswith(".pdf") or not fname.upper().startswith("SBI") or fname in seen:
                        continue
                    seen.add(fname)
                    path = os.path.abspath(os.path.join(settings.INVOICE_STORAGE_PATH, f"ework_{tag}_{fname}"))
                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    files.append(path)
                    print(f"Downloaded Ework self-billing invoice: {os.path.basename(path)} (mailbox {user.split('@')[0][:3]}***)")
            mail.logout()
        except Exception as e:
            print(f"Ework fetch from one mailbox failed: {e}")
    return files


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
        
        # Payment-period rule: Wolt / Foodora / Uber pay ~2 weeks late, so the invoices that belong
        # to a payment month are the ones RECEIVED from the last two weeks of the previous month
        # up to the end of the target month.
        month_start, month_end = payment_window(year, month)

        since_str  = month_start.strftime("%d-%b-%Y")
        before_str = month_end.strftime("%d-%b-%Y")

        date_criteria = f'(SINCE "{since_str}" BEFORE "{before_str}")'
        print(f"Fetching emails RECEIVED between {since_str} and {before_str} (payout month: {year}-{month:02d})")
        received_index = load_received_index()

        processed_ids = set()
        # FIXED: Search by partner and email received date only
        # Removed all work period date filtering from subjects
        queries = [
            (f'(SUBJECT "Wolt payout report" {date_criteria})', "wolt"),
            (f'(SUBJECT "underlag" SUBJECT "Foodora" {date_criteria})', "foodora"),
            (f'(FROM "restaurants.sweden@uber.com" {date_criteria})', "ubereats"),
        ]

        # Uber Eats (current format): weekly "utbetalningssammanfattning" mails from noreply@uber.com.
        # The official monthly statement PDF for month M is attached to a mail sent in the first
        # days of month M+1, so look a little past the end of the month for it.
        try:
            uber_files = _fetch_uber_invoices(mail, year, month, month_start, month_end, received_index)
            downloaded_files.extend(uber_files)
        except Exception as e:
            print(f"Uber email fetch failed: {e}")

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
                    try:
                        received_date = email.utils.parsedate_to_datetime(msg.get("Date")).date().isoformat()
                    except Exception:
                        received_date = None
                    
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
                            
                            if received_date:
                                received_index[safe_filename] = received_date
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
                            if received_date:
                                received_index[safe_filename] = received_date
                            downloaded_files.append(os.path.abspath(filepath))
                            print(f"Generated PDF from email body: {safe_filename}")
                    elif not found_pdf:
                        print(f"Skipping {partner_tag} email without PDF attachment (likely promotional): {subject[:50]}")

        mail.close()
        mail.logout()
        save_received_index(received_index)

        try:
            downloaded_files.extend(_fetch_ework_invoices(year, month, month_start, month_end))
        except Exception as e:
            print(f"Ework invoice fetch failed: {e}")
    except Exception as e:
        print(f"Error fetching emails: {e}")

    return downloaded_files
