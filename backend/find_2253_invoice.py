#!/usr/bin/env python3
"""
Find the missing Uber Eats 2253 kr invoice for July 2026
"""
import imaplib
import email
import re
import os

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

def find_2253_invoice():
    """Search for the 2253 kr Uber Eats invoice."""
    
    EMAIL_HOST = "imap.gmail.com"
    EMAIL_USER = "hongyanab@gmail.com"
    EMAIL_PASS = "ufbeqmmlpjrjonqv"
    
    print("Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    
    # Search for Uber emails in July 2026
    print("Searching for Uber Eats emails received in July 2026...")
    result, data = mail.search(None, '(FROM "restaurants.sweden@uber.com" SINCE "01-Jul-2026" BEFORE "01-Aug-2026")')
    
    if result != "OK":
        print("Search failed")
        return
    
    email_ids = data[0].split()
    print(f"Found {len(email_ids)} Uber emails in July 2026\n")
    
    output_dir = "./invoices"
    os.makedirs(output_dir, exist_ok=True)
    
    found_2253 = False
    
    for num in email_ids:
        result, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        
        subject = msg.get("Subject", "")
        date_header = msg.get("Date", "")
        
        # Get HTML body (Uber sends HTML emails)
        body = get_html_body(msg)
        
        # Look for amount
        amount_match = re.search(r'Total\s+Betalning\s+(-?[0-9\s.,]+)\s*kr', body, re.IGNORECASE)
        
        if amount_match:
            amount_str = amount_match.group(1).strip()
            # Clean amount (remove spaces)
            clean_amount = amount_str.replace(" ", "").replace(",", ".")
            
            print(f"Email #{num.decode()}")
            print(f"  Date: {date_header[:50]}")
            print(f"  Subject: {subject[:80]}")
            print(f"  Amount: {amount_str} kr (clean: {clean_amount})")
            
            # Check if this is the 2253 kr invoice
            if "2253" in clean_amount or "2 253" in amount_str:
                print(f"  >>> FOUND THE 2253 kr INVOICE!")
                found_2253 = True
                
                # Save email details
                print(f"\n{'='*60}")
                print("EMAIL DETAILS:")
                print(f"{'='*60}")
                print(f"Subject: {subject}")
                print(f"Date: {date_header}")
                print(f"Amount: {amount_str} kr")
                print(f"\nBody excerpt:")
                print(body[:500])
                print(f"{'='*60}\n")
            print()
    
    mail.close()
    mail.logout()
    
    if not found_2253:
        print("❌ The 2253 kr invoice was NOT found in July 2026 emails")
        print("\nPossible reasons:")
        print("1. The email was received in a different month (June or August)")
        print("2. The email was deleted or moved to a different folder")
        print("3. The amount is different (check if it's actually a different value)")
    else:
        print("✅ Successfully found and generated the 2253 kr invoice!")

if __name__ == "__main__":
    find_2253_invoice()
