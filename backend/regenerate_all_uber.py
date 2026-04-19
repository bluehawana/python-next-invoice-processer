#!/usr/bin/env python3
"""
Regenerate all Uber Eats invoices with the updated format
"""
import imaplib
import email
import os
import re
from email.header import decode_header
from email_module import get_html_body, create_email_pdf, settings

def regenerate_uber_invoices():
    """Fetch all Uber emails and regenerate PDFs with proper format"""
    
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        print("Email credentials not set")
        return
    
    print(f"Connecting to {settings.EMAIL_HOST}...")
    mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
    mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
    mail.select("inbox")
    
    # Search for all Uber emails
    result, data = mail.search(None, '(FROM "restaurants.sweden@uber.com")')
    
    if result != "OK":
        print("Search failed")
        return
    
    email_ids = data[0].split()
    print(f"Found {len(email_ids)} Uber Eats emails")
    
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)
    
    regenerated = 0
    skipped = 0
    
    for num in email_ids:
        result, data = mail.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Decode subject
        subj_raw = msg.get("Subject", "")
        decoded_parts = decode_header(subj_raw)
        subject = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                subject += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                subject += part
        
        # Get email body
        body = get_html_body(msg)
        if not body.strip():
            print(f"Skipping email {num.decode()} - no body content")
            skipped += 1
            continue
        
        # Extract Total Betalning to use in filename
        total_match = re.search(r'Total\s+Betalning\s+(-?[0-9.,]+)\s*kr', body, re.IGNORECASE)
        if total_match:
            amount = total_match.group(1).replace(" ", "").replace(",", ".")
            filename = f"ubereats_{amount}.pdf"
        else:
            filename = f"ubereats_{num.decode()}_email_body.pdf"
        
        filepath = os.path.join(settings.INVOICE_STORAGE_PATH, filename)
        
        try:
            create_email_pdf(subject, body, filepath, "ubereats")
            print(f"✓ Regenerated: {filename}")
            regenerated += 1
        except Exception as e:
            print(f"✗ Failed to generate {filename}: {e}")
            skipped += 1
    
    mail.close()
    mail.logout()
    
    print(f"\n=== Summary ===")
    print(f"Regenerated: {regenerated}")
    print(f"Skipped: {skipped}")
    print(f"Total: {len(email_ids)}")

if __name__ == "__main__":
    regenerate_uber_invoices()
