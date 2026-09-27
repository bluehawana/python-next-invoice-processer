#!/usr/bin/env python3
"""
FULLY AUTOMATED INVOICE SYNC
Just provide a photo of handwritten records - everything else is automatic!

Usage: python auto_sync.py <year> <month> <photo_path>
Example: python auto_sync.py 2026 8 ~/Downloads/IMG_2766.heic
"""
import sys
import os
from typing import Dict, List
from datetime import datetime, date
from ocr_module import process_handwritten_image, extract_payout_amount_from_pdf
from email_module import fetch_email_invoices
from stripe_module import download_stripe_payouts, generate_payout_reports, settings
from fpdf import FPDF

def create_uber_invoice_auto(amount: float, week_num: int, year: int, month: int) -> str:
    """Auto-create Uber invoice with estimated dates"""
    
    # Estimate week dates based on week number
    day_start = 1 + (week_num - 1) * 7
    day_end = min(day_start + 6, 31)
    
    start_date = f"{year}-{month:02d}-{day_start:02d}"
    end_date = f"{year}-{month:02d}-{day_end:02d}"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(30, 10, "UBER", ln=False)
    pdf.set_font("Arial", "", 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "EATS", ln=True)
    pdf.ln(8)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Ichiban Sushi", ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Betalningsoversikt over {start_date} - {end_date}", ln=True)
    pdf.ln(8)
    
    # Boxes
    y_start = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(105, y_start, 95, 30)
    pdf.set_xy(105, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "Total Betalning", align='C', ln=True)
    pdf.set_xy(105, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(6, 149, 55)
    
    amount_str = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    pdf.cell(95, 12, f"{amount_str} kr", align='C')
    pdf.set_y(y_start + 38)
    
    # Footer
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4, "Auto-generated from handwritten records".encode('latin-1', 'replace').decode('latin-1'))
    
    filename = f"ubereats_{year}{month:02d}_week{week_num}_{amount:.2f}_auto.pdf"
    filepath = os.path.join(settings.INVOICE_STORAGE_PATH, filename)
    pdf.output(filepath)
    
    return filepath

def auto_sync(year: int, month: int, image_path: str):
    """Fully automated sync from handwritten photo"""
    
    print("\n" + "="*80)
    print(f"🚀 FULLY AUTOMATED INVOICE SYNC - {year}-{month:02d}")
    print("="*80)
    
    # STEP 1: OCR - Extract from handwritten
    print("\n📸 Step 1: Processing handwritten photo...")
    print(f"   Image: {os.path.basename(image_path)}")
    
    handwritten = process_handwritten_image(image_path)
    
    if not handwritten:
        print("❌ OCR failed! Cannot proceed.")
        return False
    
    print("   ✅ OCR Success!")
    for partner, amounts in handwritten.items():
        print(f"      {partner}: {len(amounts)} invoices = {sum(amounts):,.2f} kr")
    
    # STEP 2: Fetch from emails
    print("\n📧 Step 2: Fetching invoices from emails...")
    email_files = fetch_email_invoices(year, month)
    print(f"   ✅ Found {len(email_files)} email invoices")
    
    # STEP 3: Fetch Stripe
    print("\n💳 Step 3: Fetching Stripe payouts...")
    stripe_payouts = download_stripe_payouts(year, month)
    print(f"   ✅ Found {len(stripe_payouts)} Stripe payouts")
    
    # Generate Stripe PDFs if needed
    if stripe_payouts:
        print("   Generating Stripe PDFs...")
        payout_ids = [p['id'] for p in stripe_payouts]
        stripe_pdfs = []
        try:
            import asyncio
            stripe_pdfs = asyncio.run(generate_payout_reports(payout_ids))
            print(f"   ✅ Generated {len(stripe_pdfs)} Stripe PDFs")
        except Exception as e:
            print(f"   ⚠️ Stripe PDF generation error: {e}")
    
    # STEP 4: Extract amounts from existing PDFs
    print("\n🔍 Step 4: Analyzing existing invoices...")
    
    found_amounts = {
        'Uber': [],
        'Wolt': [],
        'Foodora': [],
        'Stripe': []
    }
    
    for file in email_files:
        filename = os.path.basename(file).lower()
        amount = None
        
        if 'uber' in filename:
            amount = extract_payout_amount_from_pdf(file, 'Uber')
            if amount:
                found_amounts['Uber'].append(amount)
        elif 'wolt' in filename:
            amount = extract_payout_amount_from_pdf(file, 'Wolt')
            if amount:
                found_amounts['Wolt'].append(amount)
        elif 'foodora' in filename:
            amount = extract_payout_amount_from_pdf(file, 'Foodora')
            if amount:
                found_amounts['Foodora'].append(amount)
    
    # Add Stripe amounts
    found_amounts['Stripe'] = [p['amount'] for p in stripe_payouts]
    
    print("   Found in system:")
    for partner, amounts in found_amounts.items():
        if amounts:
            print(f"      {partner}: {len(amounts)} invoices = {sum(amounts):,.2f} kr")
    
    # STEP 5: AUTO-CREATE MISSING INVOICES
    print("\n🤖 Step 5: Auto-creating missing invoices...")
    
    created_count = 0
    
    # Check Uber
    handwritten_uber = handwritten.get('Uber', []) or handwritten.get('UberEats', []) or handwritten.get('Ubereats', [])
    if handwritten_uber and len(found_amounts['Uber']) < len(handwritten_uber):
        print(f"\n   🚗 Uber Eats: Creating {len(handwritten_uber)} missing invoices...")
        for i, amount in enumerate(handwritten_uber, 1):
            if amount not in found_amounts['Uber']:
                filepath = create_uber_invoice_auto(amount, i, year, month)
                print(f"      ✅ Created: {os.path.basename(filepath)}")
                created_count += 1
    
    # STEP 6: FINAL RECONCILIATION
    print("\n" + "="*80)
    print("📊 FINAL RECONCILIATION")
    print("="*80)
    
    # Re-scan all invoices
    all_files = []
    if os.path.exists(settings.INVOICE_STORAGE_PATH):
        for f in os.listdir(settings.INVOICE_STORAGE_PATH):
            if f.endswith('.pdf'):
                all_files.append(os.path.join(settings.INVOICE_STORAGE_PATH, f))
    
    print(f"\nTotal invoices in system: {len(all_files)}")
    print(f"Created this run: {created_count}")
    
    # Match handwritten vs found
    all_matched = True
    for partner in ['Uber', 'Wolt', 'Foodora', 'Stripe']:
        hw_key = partner
        if partner == 'Uber':
            hw_amounts = handwritten.get('Uber', []) or handwritten.get('UberEats', []) or handwritten.get('Ubereats', [])
        elif partner == 'Stripe':
            hw_amounts = handwritten.get('Stripe', []) or handwritten.get('Hem', []) or handwritten.get('Ichiban', [])
        else:
            hw_amounts = handwritten.get(partner, [])
        
        if not hw_amounts:
            continue
        
        found_total = sum(found_amounts.get(partner, []))
        hw_total = sum(hw_amounts)
        
        status = "✅" if abs(found_total - hw_total) < 1.0 else "⚠️"
        
        print(f"\n{status} {partner}:")
        print(f"   Handwritten: {len(hw_amounts)} invoices = {hw_total:,.2f} kr")
        print(f"   Found:       {len(found_amounts.get(partner, []))} invoices = {found_total:,.2f} kr")
        
        if abs(found_total - hw_total) >= 1.0:
            all_matched = False
            diff = hw_total - found_total
            print(f"   ⚠️ Difference: {diff:,.2f} kr")
    
    print("\n" + "="*80)
    if all_matched:
        print("🎉 SUCCESS: All invoices synced automatically!")
    else:
        print("⚠️ WARNING: Some discrepancies found - manual review needed")
    print("="*80 + "\n")
    
    return all_matched

def main():
    if len(sys.argv) < 4:
        print("Usage: python auto_sync.py <year> <month> <photo_path>")
        print("Example: python auto_sync.py 2026 8 ~/Downloads/IMG_2766.heic")
        sys.exit(1)
    
    year = int(sys.argv[1])
    month = int(sys.argv[2])
    image_path = os.path.expanduser(sys.argv[3])
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)
    
    success = auto_sync(year, month, image_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
