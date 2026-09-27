#!/usr/bin/env python3
"""
Smart Invoice Sync - Complete workflow to prevent missing invoices

Workflow:
1. Upload handwritten paper → OCR
2. Fetch from emails
3. If missing → Fetch from partner portals
4. Reconcile & generate invoices
5. Alert if still missing
"""
import os
import sys
from typing import Dict, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import modules
from ocr_module import process_handwritten_image, reconcile_invoices
from email_module import fetch_email_invoices
from stripe_module import download_stripe_payouts
from invoice_checker import InvoiceChecker

class SmartInvoiceSync:
    def __init__(self, year: int, month: int):
        self.year = year
        self.month = month
        self.handwritten_data = {}
        self.email_invoices = []
        self.missing_partners = []
        
    def step1_process_handwritten(self, image_path: str) -> bool:
        """Step 1: Process handwritten paper with OCR"""
        print("\n" + "="*80)
        print("STEP 1: PROCESS HANDWRITTEN RECORDS")
        print("="*80)
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return False
        
        print(f"📸 Processing: {image_path}")
        self.handwritten_data = process_handwritten_image(image_path)
        
        if not self.handwritten_data:
            print("❌ OCR failed or no data extracted")
            return False
        
        print("\n✅ Handwritten data extracted:")
        for partner, amounts in self.handwritten_data.items():
            total = sum(amounts)
            print(f"   {partner}: {len(amounts)} invoices, Total: {total:,.2f} SEK")
        
        return True
    
    def step2_fetch_from_emails(self) -> bool:
        """Step 2: Fetch invoices from emails"""
        print("\n" + "="*80)
        print("STEP 2: FETCH INVOICES FROM EMAILS")
        print("="*80)
        
        self.email_invoices = fetch_email_invoices(self.year, self.month)
        
        print(f"\n✅ Found {len(self.email_invoices)} invoices in emails")
        
        return True
    
    def step3_check_completeness(self) -> List[str]:
        """Step 3: Check which partners are missing invoices"""
        print("\n" + "="*80)
        print("STEP 3: CHECK INVOICE COMPLETENESS")
        print("="*80)
        
        checker = InvoiceChecker(self.year, self.month)
        
        uber_result = checker.check_uber_eats()
        foodora_result = checker.check_foodora()
        wolt_result = checker.check_wolt()
        
        missing = []
        
        # Check if any partner has 0 emails when handwritten data exists
        if 'Uber' in self.handwritten_data or 'UberEats' in self.handwritten_data:
            if uber_result['emails_found'] == 0:
                missing.append('uber')
                print("⚠️ Uber Eats: Invoices expected but NOT found in emails")
        
        if 'Foodora' in self.handwritten_data:
            if foodora_result['emails_found'] < 2:
                missing.append('foodora')
                print("⚠️ Foodora: Incomplete invoices in emails")
        
        if 'Wolt' in self.handwritten_data:
            if wolt_result['emails_found'] < 2:
                missing.append('wolt')
                print("⚠️ Wolt: Incomplete invoices in emails")
        
        self.missing_partners = missing
        
        if missing:
            print(f"\n❌ Missing invoices from: {', '.join(missing)}")
        else:
            print("\n✅ All expected invoices found in emails!")
        
        return missing
    
    def step4_fetch_from_portals(self) -> bool:
        """Step 4: Fetch missing invoices from partner portals"""
        if not self.missing_partners:
            print("\n⏭️  STEP 4: SKIPPED - No missing invoices")
            return True
        
        print("\n" + "="*80)
        print("STEP 4: FETCH MISSING INVOICES FROM PARTNER PORTALS")
        print("="*80)
        
        print("\n⚠️ MANUAL ACTION REQUIRED:")
        print("   Partner portal scraping requires manual login (2FA, captcha, etc.)")
        print("\n   Please manually download missing invoices from:")
        
        if 'uber' in self.missing_partners:
            print("\n   🚗 Uber Eats:")
            print("      1. Go to: https://restaurant.uber.com/payments")
            print("      2. Filter by date range")
            print(f"      3. Download weekly reports for {self.year}-{self.month:02d}")
            print("      4. Save to: ./portal_downloads/")
        
        if 'foodora' in self.missing_partners:
            print("\n   🍕 Foodora:")
            print("      1. Go to: https://partner.foodora.se")
            print("      2. Navigate to invoices/payments section")
            print(f"      3. Download invoices for {self.year}-{self.month:02d}")
            print("      4. Save to: ./portal_downloads/")
        
        if 'wolt' in self.missing_partners:
            print("\n   ⚡ Wolt:")
            print("      1. Go to: https://restaurant.wolt.com/payments")
            print(f"      2. Download payout reports for {self.year}-{self.month:02d}")
            print("      3. Save to: ./portal_downloads/")
        
        print("\n   Press Enter when you've downloaded the missing invoices...")
        input()
        
        # Check if files were downloaded
        portal_dir = "./portal_downloads"
        if os.path.exists(portal_dir):
            portal_files = os.listdir(portal_dir)
            print(f"\n✅ Found {len(portal_files)} files in portal_downloads/")
            # Move files to main invoices folder
            import shutil
            from stripe_module import settings
            for file in portal_files:
                src = os.path.join(portal_dir, file)
                dst = os.path.join(settings.INVOICE_STORAGE_PATH, file)
                shutil.move(src, dst)
                print(f"   Moved: {file}")
        
        return True
    
    def step5_reconcile(self) -> bool:
        """Step 5: Reconcile all invoices"""
        print("\n" + "="*80)
        print("STEP 5: RECONCILE INVOICES")
        print("="*80)
        
        # Get all files
        from stripe_module import settings
        all_files = []
        if os.path.exists(settings.INVOICE_STORAGE_PATH):
            for f in os.listdir(settings.INVOICE_STORAGE_PATH):
                if f.endswith('.pdf'):
                    all_files.append(os.path.join(settings.INVOICE_STORAGE_PATH, f))
        
        # Get Stripe payouts
        stripe_payouts = download_stripe_payouts(self.year, self.month)
        
        # Reconcile
        results = reconcile_invoices(self.handwritten_data, stripe_payouts, all_files)
        
        print(f"\n📊 RECONCILIATION RESULTS:")
        print("-"*80)
        
        all_matched = True
        for rec in results:
            partner = rec['partner']
            status = "✅" if rec['reconciled'] else "❌"
            matched = rec['matched_count']
            expected = rec['handwritten_count']
            
            print(f"{status} {partner}: {matched}/{expected} matched")
            
            if not rec['reconciled']:
                all_matched = False
                if matched == 0:
                    print(f"   ⚠️ NO invoices found - check manually!")
                else:
                    print(f"   ⚠️ {expected - matched} invoices still missing")
        
        print("-"*80)
        
        if all_matched:
            print("\n🎉 SUCCESS: All invoices reconciled!")
        else:
            print("\n⚠️ WARNING: Some invoices still missing - manual review needed")
        
        return all_matched
    
    def run_full_workflow(self, image_path: str) -> bool:
        """Run the complete workflow"""
        print("\n" + "="*80)
        print(f"SMART INVOICE SYNC - {self.year}-{self.month:02d}")
        print("="*80)
        print("This workflow ensures NO invoices are missed!\n")
        
        # Step 1: OCR
        if not self.step1_process_handwritten(image_path):
            return False
        
        # Step 2: Fetch from emails
        self.step2_fetch_from_emails()
        
        # Step 3: Check completeness
        self.step3_check_completeness()
        
        # Step 4: Fetch from portals (if needed)
        self.step4_fetch_from_portals()
        
        # Step 5: Reconcile
        success = self.step5_reconcile()
        
        print("\n" + "="*80)
        if success:
            print("✅ WORKFLOW COMPLETE - All invoices accounted for!")
        else:
            print("⚠️ WORKFLOW COMPLETE - Manual review required")
        print("="*80 + "\n")
        
        return success


def main():
    if len(sys.argv) < 4:
        print("Usage: python smart_invoice_sync.py <year> <month> <handwritten_image_path>")
        print("Example: python smart_invoice_sync.py 2026 8 ~/Downloads/IMG_2766.heic")
        sys.exit(1)
    
    year = int(sys.argv[1])
    month = int(sys.argv[2])
    image_path = os.path.expanduser(sys.argv[3])
    
    sync = SmartInvoiceSync(year, month)
    sync.run_full_workflow(image_path)


if __name__ == "__main__":
    main()
