#!/usr/bin/env python3
import imaplib
import email
import re
import os
from fpdf import FPDF
from stripe_module import settings

EMAIL_HOST = "imap.gmail.com"
EMAIL_USER = "hongyanab@gmail.com"
EMAIL_PASS = "ufbeqmmlpjrjonqv"


def clean_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')


def create_uber_invoice_pdf(subject, body, start_date, end_date, num, filepath):
    """Create Uber Eats invoice PDF."""
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

    # Date range
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Betaltingsoversikt over {start_date} - {end_date}", ln=True)
    pdf.ln(3)

    # Greeting
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Hej Ichiban Sushi,", ln=True)
    pdf.ln(2)
    pdf.multi_cell(0, 5, clean_text("Vi hoppas att du har en bra vecka. Nedan hittar du din veckovisa betalningsoversikt. Fakturan for ovan namnda period finns redan tillganglig i Uber Eats Manager."))
    pdf.ln(2)
    pdf.cell(0, 5, "Tack for att du ar en partner,", ln=True)
    pdf.cell(0, 5, "Uber Eats-teamet", ln=True)
    pdf.ln(8)

    # Total forsäljning
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Total forsäljning", ln=True)
    pdf.ln(3)

    # Extract values from body
    total_match = re.search(r'Total Betalning[:\s]*([0-9.,]+)\s*kr', body, re.IGNORECASE)
    orders_match = re.search(r'Bestallningar\s*(\d+)', body, re.IGNORECASE)

    total_amount = total_match.group(1) if total_match else "0,00"
    num_orders = orders_match.group(1) if orders_match else "0"

    y_start = pdf.get_y()

    # Box 1
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, y_start, 90, 30)
    pdf.set_xy(10, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(90, 5, "Bestallningar", align='C', ln=True)
    pdf.set_xy(10, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 12, num_orders, align='C')

    # Box 2
    pdf.rect(105, y_start, 95, 30)
    pdf.set_xy(105, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "Total Betalning", align='C', ln=True)
    pdf.set_xy(105, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(6, 149, 55)
    pdf.cell(95, 12, f"{total_amount} kr", align='C')

    pdf.set_y(y_start + 38)

    # Betalningsberakning
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Betalningsberakning", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 6, "DAG/UPPHANTNINGSTID", ln=False)
    pdf.cell(40, 6, "Bestallningar", align='C', ln=False)
    pdf.cell(0, 6, "FORSALJNING (EFTER SKATT)", align='R', ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)

    for line in body.split('\n'):
        day_match = re.match(r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d+)\s+([0-9.,]+)\s*kr', line.strip())
        if day_match:
            pdf.cell(60, 6, day_match.group(1), ln=False)
            pdf.cell(40, 6, day_match.group(2), align='C', ln=False)
            pdf.cell(0, 6, f"{day_match.group(3)} kr", align='R', ln=True)

    pdf.ln(3)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    def add_summary_line(label, value, bold=False):
        if bold:
            pdf.set_font("Arial", "B", 10)
        else:
            pdf.set_font("Arial", "", 9)
        pdf.cell(100, 6, "", ln=False)
        pdf.cell(50, 6, label, ln=False)
        pdf.cell(0, 6, value, align='R', ln=True)

    totalbelopp = re.search(r'Totalbelopp\s*([0-9.,]+)\s*kr', body)
    uber_fee = re.search(r'Uber Eats-avgift\s*(-?[0-9.,]+)\s*kr', body)
    moms = re.search(r'Moms pa Uber Eats-avgift\s*(-?[0-9.,]+)\s*kr', body)
    netto = re.search(r'Nettoforsaljning\s*([0-9.,]+)\s*kr', body)

    if totalbelopp:
        add_summary_line("Totalbelopp", f"{totalbelopp.group(1)} kr")
    if uber_fee:
        add_summary_line("Uber Eats-avgift", f"{uber_fee.group(1)} kr")
    if moms:
        add_summary_line("Moms pa Uber Eats-avgift", f"{moms.group(1)} kr")
    if netto:
        add_summary_line("Nettoforsaljning", f"{netto.group(1)} kr")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "", ln=False)
    pdf.set_text_color(6, 149, 55)
    pdf.cell(50, 10, "Total Betalning", ln=False)
    pdf.cell(0, 10, f"{total_amount} kr", align='R', ln=True)

    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)
    pdf.output(filepath)
    return filepath


def main():
    print("Connecting to email...")
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    result, data = mail.search(None, 'FROM "restaurants.sweden@uber.com"')
    all_ids = data[0].split()
    print(f"Found {len(all_ids)} Uber emails")

    for num in all_ids:
        result, data = mail.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject = msg.get("Subject", "")

        if '1/19/26' in subject and '1/25/26' in subject:
            print(f"\n--- Processing: {subject}")
            body = get_body(msg)
            filepath = create_uber_invoice_pdf(subject, body, "1/19/26", "1/25/26", num,
                os.path.join(settings.INVOICE_STORAGE_PATH, "ubereats_102375_email_body.pdf"))
            print(f"Created: {filepath}")
        elif '1/12/26' in subject and '1/18/26' in subject:
            print(f"\n--- Processing: {subject}")
            body = get_body(msg)
            filepath = create_uber_invoice_pdf(subject, body, "1/12/26", "1/18/26", num,
                os.path.join(settings.INVOICE_STORAGE_PATH, "ubereats_210210_email_body.pdf"))
            print(f"Created: {filepath}")

    mail.logout()
    print("\nDone!")


def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break
                except:
                    pass
    return body


if __name__ == "__main__":
    main()
