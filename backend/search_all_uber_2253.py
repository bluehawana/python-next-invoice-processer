#!/usr/bin/env python3
"""
Search for the 2253 kr Uber Eats invoice across all months
"""
import imaplib
import email
import re

def get_html_body(msg):
    """Extract HTML body from email."""
    html = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
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

def search_all_uber():
    EMAIL_HOST = "imap.gmail.com"
    EMAIL_USER = "hongyanab@gmail.com"
    EMAIL_PASS = "ufbeqmmlpjrjonqv"
    
    print("Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    
    # Search for ALL Uber emails in 2026
    print("Searching for ALL Uber Eats emails in 2026...")
    result, data = mail.search(None, '(FROM "restaurants.sweden@uber.com" SINCE "01-Jan-2026" BEFORE "01-Jan-2027")')
    
    if result != "OK":
        print("Search failed")
        return
    
    email_ids = data[0].split()
    print(f"Found {len(email_ids)} Uber emails in 2026\n")
    
    all_amounts = []
    found_2253 = False
    
    for num in email_ids:
        result, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        
        subject = msg.get("Subject", "")
        date_header = msg.get("Date", "")
        
        body = get_html_body(msg)
        amount_match = re.search(r'Total\s+Betalning\s+(-?[0-9\s.,]+)\s*kr', body, re.IGNORECASE)
        
        if amount_match:
            amount_str = amount_match.group(1).strip()
            clean_amount = amount_str.replace(" ", "").replace(",", ".")
            
            all_amounts.append({
                'id': num.decode(),
                'date': date_header[:25],
                'amount': amount_str,
                'subject': subject[:60]
            })
            
            if "2253" in clean_amount or "2 253" in amount_str:
                print(f"✅ FOUND THE 2253 kr INVOICE!")
                print(f"  Email ID: #{num.decode()}")
                print(f"  Date: {date_header}")
                print(f"  Subject: {subject}")
                print(f"  Amount: {amount_str} kr")
                print()
                found_2253 = True
    
    mail.close()
    mail.logout()
    
    # Print all amounts sorted by date
    print(f"\n{'='*80}")
    print("ALL UBER EATS INVOICES IN 2026:")
    print(f"{'='*80}")
    for inv in all_amounts:
        marker = " <<<< TARGET" if "2253" in inv['amount'] or "2 253" in inv['amount'] else ""
        print(f"{inv['date']} | {inv['amount']:>15} kr | #{inv['id']}{marker}")
    
    print(f"\n{'='*80}")
    if not found_2253:
        print("❌ The 2253 kr invoice was NOT found in ANY 2026 emails")
        print("\nClosest amounts found:")
        # Find amounts close to 2253
        for inv in all_amounts:
            amount_num = float(inv['amount'].replace(" ", "").replace(",", ".").replace(".", ""))
            if 2000 <= amount_num <= 2500:
                print(f"  {inv['amount']} kr on {inv['date']}")
    else:
        print("✅ Found the 2253 kr invoice!")

if __name__ == "__main__":
    search_all_uber()
