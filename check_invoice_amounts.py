#!/usr/bin/env python3
"""
Check extracted amounts from existing invoice PDFs
"""
import os
import re
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using pypdf."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[PDF] Could not extract text from {os.path.basename(pdf_path)}: {e}")
        return ""

def extract_amount_from_text(text: str, filename: str) -> float:
    """Extract amount from PDF text."""
    filename_lower = filename.lower()
    
    # Check for Stripe payout amounts
    if "stripe" in filename_lower:
        pattern = r'([\d,]+\.\d{2})kr\s+SEK'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
    
    # Check for Wolt amounts
    if "wolt" in filename_lower:
        pattern = r'Belopp\s+utbetalning\s+([\d\s]+[.,]\d{2})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(' ', '').replace(',', '.')
            return float(amount_str)
    
    # Check for Foodora amounts
    if "foodora" in filename_lower:
        pattern = r'Vi\s+betalar\s+ut\s+till\s+er.*?([\d,]+\.\d{2})\s*SEK'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
    
    # Check for Uber Eats amounts
    if "ubereats" in filename_lower:
        pattern = r'Total\s+Betalning\s+([\d.]+,\d{2})\s*kr'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace('.', '').replace(',', '.')
            return float(amount_str)
    
    return 0.0

def main():
    invoice_dir = "/Users/harvad/Projects/python-next-invoice-processer/backend/invoices"
    
    # Check all subdirectories
    all_files = []
    for root, dirs, files in os.walk(invoice_dir):
        for file in files:
            if file.endswith('.pdf'):
                all_files.append(os.path.join(root, file))
    
    print(f"Found {len(all_files)} PDF files")
    print("\nChecking amounts:")
    
    amounts_by_partner = {
        'Stripe': [],
        'Wolt': [],
        'Foodora': [],
        'Uber': []
    }
    
    for pdf_path in all_files:
        filename = os.path.basename(pdf_path)
        text = extract_text_from_pdf(pdf_path)
        
        # Determine partner
        partner = "Unknown"
        if "stripe" in filename.lower():
            partner = "Stripe"
        elif "wolt" in filename.lower():
            partner = "Wolt"
        elif "foodora" in filename.lower():
            partner = "Foodora"
        elif "ubereats" in filename.lower():
            partner = "Uber"
        
        amount = extract_amount_from_text(text, filename)
        
        if amount > 0:
            amounts_by_partner[partner].append(amount)
            print(f"{partner}: {filename} → {amount:.2f} SEK")
        else:
            print(f"{partner}: {filename} → Could not extract amount")
    
    print("\n" + "="*50)
    print("Summary by partner:")
    for partner, amounts in amounts_by_partner.items():
        if amounts:
            total = sum(amounts)
            print(f"{partner}: {len(amounts)} invoices, total: {total:.2f} SEK, amounts: {', '.join(f'{a:.2f}' for a in amounts)}")
    
    print("\n" + "="*50)
    print("Looking for specific missing amounts:")
    print("Missing: Stripe 630.90, Uber 228.80, Uber 667.55, Foodora 9667.82")
    
    # Check if any amounts are close to missing ones
    all_amounts = []
    for partner, amounts in amounts_by_partner.items():
        all_amounts.extend([(partner, amount) for amount in amounts])
    
    missing_targets = [("Stripe", 630.90), ("Uber", 228.80), ("Uber", 667.55), ("Foodora", 9667.82)]
    
    for target_partner, target_amount in missing_targets:
        print(f"\nLooking for {target_partner} amount {target_amount:.2f}:")
        found = False
        for partner, amount in all_amounts:
            if partner == target_partner and abs(amount - target_amount) < 0.5:  # 0.5 SEK tolerance
                print(f"  ✓ Found: {amount:.2f} in {partner}")
                found = True
                break
        if not found:
            print(f"  ✗ Missing: {target_amount:.2f} not found in {target_partner} invoices")

if __name__ == "__main__":
    main()