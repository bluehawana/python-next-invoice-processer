#!/usr/bin/env python3
"""
Simple script to generate all invoices for a specific month.
Usage: python generate_invoices.py [year] [month]
Example: python generate_invoices.py 2026 3
"""
import sys
import os
import asyncio
from stripe_module import download_stripe_payouts, generate_payout_reports, settings
from email_module import fetch_email_invoices

async def generate_all_invoices(year: int, month: int, output_dir: str = None):
    """Generate all invoices for the specified month."""
    
    if output_dir is None:
        output_dir = settings.INVOICE_STORAGE_PATH
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Generating invoices for {year}-{month:02d}")
    print(f"{'='*60}\n")
    
    # 1. Stripe payouts
    print("📊 Fetching Stripe payouts...")
    st_payouts = download_stripe_payouts(year, month)
    payout_ids = [p['id'] for p in st_payouts]
    
    stripe_pdfs = []
    if payout_ids:
        print(f"   Found {len(payout_ids)} payouts")
        print("   Generating PDFs...")
        try:
            # Temporarily change output directory
            original_path = settings.INVOICE_STORAGE_PATH
            settings.INVOICE_STORAGE_PATH = output_dir
            
            stripe_pdfs = await generate_payout_reports(payout_ids)
            
            settings.INVOICE_STORAGE_PATH = original_path
            
            print(f"   ✓ Generated {len(stripe_pdfs)} Stripe invoices")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    else:
        print("   No Stripe payouts found")
    
    print()
    
    # 2. Email invoices (Uber, Wolt, Foodora)
    print("📧 Fetching email invoices...")
    
    # Temporarily change output directory
    original_path = settings.INVOICE_STORAGE_PATH
    settings.INVOICE_STORAGE_PATH = output_dir
    
    email_files = fetch_email_invoices(year, month)
    
    settings.INVOICE_STORAGE_PATH = original_path
    
    print(f"   ✓ Generated {len(email_files)} email invoices")
    
    print()
    
    # Summary
    all_files = stripe_pdfs + email_files
    
    print(f"\n{'='*60}")
    print(f"✓ COMPLETE: Generated {len(all_files)} invoices")
    print(f"{'='*60}")
    print(f"\nStripe:  {len(stripe_pdfs)} invoices")
    print(f"Email:   {len(email_files)} invoices")
    print(f"\nSaved to: {output_dir}")
    print()
    
    # List files by type
    if stripe_pdfs:
        print("\nStripe invoices:")
        for f in stripe_pdfs:
            print(f"  - {os.path.basename(f)}")
    
    if email_files:
        print("\nEmail invoices:")
        for f in email_files:
            print(f"  - {os.path.basename(f)}")
    
    return all_files

def main():
    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: python generate_invoices.py <year> <month> [output_dir]")
        print("Example: python generate_invoices.py 2026 3")
        print("Example: python generate_invoices.py 2026 3 ~/Desktop/final")
        sys.exit(1)
    
    year = int(sys.argv[1])
    month = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    if output_dir:
        output_dir = os.path.expanduser(output_dir)
    
    # Run async function
    asyncio.run(generate_all_invoices(year, month, output_dir))

if __name__ == "__main__":
    main()
