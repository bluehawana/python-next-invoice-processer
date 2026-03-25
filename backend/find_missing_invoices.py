"""
Find and regenerate missing Uber Eats invoices: 1023.75 and 2102.10
"""
import imaplib
import email
import os
import re
from fpdf import FPDF
from stripe_module import settings

# Email credentials from .env
EMAIL_HOST = "imap.gmail.com"
EMAIL_USER = "hongyanab@gmail.com"
EMAIL_PASS = "ufbeqmmlpjrjonqv"

# Target amounts to find
TARGET_AMOUNTS = ["1023,75", "2102,10", "1023.75", "2102.10"]


def clean_text(text):
    """Clean text for PDF encoding."""
    return text.encode('latin-1', 'replace').decode('latin-1')


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

    if html:
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</tr>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</td>', '  ', html, flags=re.IGNORECASE)
        html = re.sub(r'<[^>]+>', '', html)
        html = re.sub(r'\n\s*\n', '\n\n', html)
        html = html.strip()
    return html


def create_uber_invoice_pdf(subject, body, filename):
    """Create Uber Eats invoice PDF matching the existing format."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

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
    pdf.multi_cell(0, 5, clean_text("Vi hoppas att du har en bra vecka. Nedan hittar du din veckovisa betalningsöversikt. Fakturan för ovan nämnda period finns redan tillgänglig i Uber Eats Manager."))
    pdf.ln(2)
    pdf.cell(0, 5, "Tack för att du är en partner,", ln=True)
    pdf.cell(0, 5, "Uber Eats-teamet", ln=True)
    pdf.ln(8)

    # === Total försäljning section ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Total försäljning", ln=True)
    pdf.ln(3)

    # Extract values from body
    total_match = re.search(r'Total Betalning[:\s]*([0-9.,]+)\s*kr', body, re.IGNORECASE)
    orders_match = re.search(r'Beställningar\s*(\d+)', body, re.IGNORECASE)

    total_amount = total_match.group(1) if total_match else "0,00"
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

    lines = body.split('\n')
    for line in lines:
        day_match = re.match(r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d+)\s+([0-9.,]+)\s*kr', line.strip())
        if day_match:
            pdf.cell(60, 6, day_match.group(1), ln=False)
            pdf.cell(40, 6, day_match.group(2), align='C', ln=False)
            pdf.cell(0, 6, f"{day_match.group(3)} kr", align='R', ln=True)

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

    totalbelopp = re.search(r'Totalbelopp\s*\d*\s*([0-9.,]+)\s*kr', body)
    uber_fee = re.search(r'Uber Eats-avgift\s*(-?[0-9.,]+)\s*kr', body)
    moms = re.search(r'Moms på Uber Eats-avgift\s*(-?[0-9.,]+)\s*kr', body)
    netto = re.search(r'Nettoförsäljning\s*([0-9.,]+)\s*kr', body)

    if totalbelopp:
        add_summary_line("Totalbelopp", f"{totalbelopp.group(1)} kr")
    if uber_fee:
        add_summary_line("Uber Eats-avgift", f"{uber_fee.group(1)} kr")
    if moms:
        add_summary_line("Moms på Uber Eats-avgift", f"{moms.group(1)} kr")
    if netto:
        add_summary_line("Nettoförsäljning", f"{netto.group(1)} kr")

    pdf.ln(5)

    # Final Total Betalning in green
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "", ln=False)
    pdf.set_text_color(6, 149, 55)
    pdf.cell(50, 10, "Total Betalning", ln=False)
    pdf.cell(0, 10, f"{total_amount} kr", align='R', ln=True)

    pdf.output(filename)
    return filename


def search_hongyanab_emails():
    """Search for Uber Eats invoices in hongyanab@gmail.com."""
    print(f"Connecting to {EMAIL_HOST} as {EMAIL_USER}...")

    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    # Search for all Uber Eats emails
    # Since we're searching from hongyanab's inbox, look for Uber emails
    result, data = mail.search(None, '(FROM "restaurants.sweden@uber.com")')

    if result != "OK":
        print("Failed to search emails")
        return

    print(f"Found {len(data[0].split())} Uber Eats emails")

    # Create output directory
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)

    found_invoices = []

    for num in data[0].split():
        # Fetch email
        result, data = mail.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = msg.get("Subject", "")
        print(f"\n-- Email #{num.decode()}: {subject[:80]}...")

        # Get body
        body_text = get_html_body(msg)
        if not body_text.strip():
            body_text = get_email_body(msg)

        # Check for target amounts
        for amount in TARGET_AMOUNTS:
            if amount in body_text or amount in subject:
                print(f"  >>> FOUND TARGET AMOUNT: {amount} SEK")

                # Extract date from subject for filename
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{2,4})', subject)
                if date_match:
                    filename = f"ubereats_{amount.replace('.', '').replace(',', '')}_{date_match.group(1).replace('/', '')}_email_body.pdf"
                else:
                    filename = f"ubereats_{amount.replace('.', '').replace(',', '')}_{num.decode()}_email_body.pdf"

                filepath = os.path.join(settings.INVOICE_STORAGE_PATH, filename)
                create_uber_invoice_pdf(subject, body_text, filepath)
                print(f"  >>> Generated PDF: {filepath}")
                found_invoices.append((amount, filepath))

        # Also show all amounts found in this email
        amounts_in_email = re.findall(r'Total Betalning[:\s]*([0-9.,]+)\s*kr', body_text, re.IGNORECASE)
        if amounts_in_email:
            print(f"  Amounts found: {amounts_in_email}")

    mail.close()
    mail.logout()

    return found_invoices


if __name__ == "__main__":
    print("=" * 60)
    print("Searching for missing Uber Eats invoices")
    print("Looking for amounts: 1023,75 SEK and 2102,10 SEK")
    print("=" * 60)

    found = search_hongyanab_emails()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if found:
        print("Found and generated PDFs for:")
        for amount, filepath in found:
            print(f"  - {amount} SEK: {filepath}")
    else:
        print("No matching invoices found for amounts 1023.75 or 2102.10")
        print("\nSearching for all Uber invoice amounts...")
        # Let the function print all amounts found
        search_hongyanab_emails()
