#!/usr/bin/env python3
"""
Invoice Completeness Checker & Auto-Generator
Prevents missing invoices by checking all sources and alerting on gaps
"""
import os
import imaplib
import email
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
import json

# Email credentials
EMAIL_HOST = "imap.gmail.com"
EMAIL_USER = "hongyanab@gmail.com"
EMAIL_PASS = "ufbeqmmlpjrjonqv"

class InvoiceChecker:
    def __init__(self, year: int, month: int):
        self.year = year
        self.month = month
        self.issues = []
        self.warnings = []
        
    def check_uber_eats(self) -> Dict:
        """
        Check Uber Eats invoices - should have ~4 weekly invoices per month
        """
        print(f"\n🚗 Checking Uber Eats for {self.year}-{self.month:02d}...")
        
        try:
            mail = imaplib.IMAP4_SSL(EMAIL_HOST)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            # Search for Uber emails in the target month (by RECEIVED date)
            month_start = date(self.year, self.month, 1)
            if self.month == 12:
                month_end = date(self.year + 1, 1, 1)
            else:
                month_end = date(self.year, self.month + 1, 1)
            
            since_str = month_start.strftime("%d-%b-%Y")
            before_str = month_end.strftime("%d-%b-%Y")
            
            result, data = mail.search(None, f'(FROM "restaurants.sweden@uber.com" SINCE "{since_str}" BEFORE "{before_str}")')
            
            email_count = len(data[0].split()) if data[0] else 0
            
            mail.close()
            mail.logout()
            
            # Uber typically sends 3-5 weekly emails per month
            status = "✅ OK" if email_count >= 3 else "⚠️ WARNING"
            
            result = {
                "partner": "Uber Eats",
                "emails_found": email_count,
                "expected_min": 3,
                "expected_max": 5,
                "status": status
            }
            
            if email_count == 0:
                self.issues.append(f"❌ Uber Eats: NO EMAILS found for {self.year}-{self.month:02d}")
                self.issues.append(f"   → Check Uber Eats dashboard manually: https://restaurant.uber.com")
                result["status"] = "❌ MISSING"
            elif email_count < 3:
                self.warnings.append(f"⚠️ Uber Eats: Only {email_count} emails found (expected 3-5)")
                self.warnings.append(f"   → Some weekly reports may be missing - check dashboard")
            
            return result
            
        except Exception as e:
            self.issues.append(f"❌ Uber Eats: Error checking emails: {e}")
            return {"partner": "Uber Eats", "error": str(e), "status": "❌ ERROR"}
    
    def check_foodora(self) -> Dict:
        """
        Check Foodora invoices - should have 2 semi-monthly invoices
        """
        print(f"\n🍕 Checking Foodora for {self.year}-{self.month:02d}...")
        
        try:
            mail = imaplib.IMAP4_SSL(EMAIL_HOST)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            month_start = date(self.year, self.month, 1)
            if self.month == 12:
                month_end = date(self.year + 1, 1, 1)
            else:
                month_end = date(self.year, self.month + 1, 1)
            
            since_str = month_start.strftime("%d-%b-%Y")
            before_str = month_end.strftime("%d-%b-%Y")
            
            result, data = mail.search(None, f'(SUBJECT "underlag" SUBJECT "Foodora" SINCE "{since_str}" BEFORE "{before_str}")')
            
            email_count = len(data[0].split()) if data[0] else 0
            
            mail.close()
            mail.logout()
            
            # Foodora sends 2 semi-monthly invoices
            status = "✅ OK" if email_count == 2 else "⚠️ WARNING"
            
            result = {
                "partner": "Foodora",
                "emails_found": email_count,
                "expected": 2,
                "status": status
            }
            
            if email_count == 0:
                self.issues.append(f"❌ Foodora: NO EMAILS found for {self.year}-{self.month:02d}")
                result["status"] = "❌ MISSING"
            elif email_count < 2:
                self.warnings.append(f"⚠️ Foodora: Only {email_count} emails found (expected 2)")
            
            return result
            
        except Exception as e:
            self.issues.append(f"❌ Foodora: Error checking emails: {e}")
            return {"partner": "Foodora", "error": str(e), "status": "❌ ERROR"}
    
    def check_wolt(self) -> Dict:
        """
        Check Wolt invoices - should have 2 semi-monthly invoices
        """
        print(f"\n⚡ Checking Wolt for {self.year}-{self.month:02d}...")
        
        try:
            mail = imaplib.IMAP4_SSL(EMAIL_HOST)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            month_start = date(self.year, self.month, 1)
            if self.month == 12:
                month_end = date(self.year + 1, 1, 1)
            else:
                month_end = date(self.year, self.month + 1, 1)
            
            since_str = month_start.strftime("%d-%b-%Y")
            before_str = month_end.strftime("%d-%b-%Y")
            
            result, data = mail.search(None, f'(SUBJECT "Wolt payout report" SINCE "{since_str}" BEFORE "{before_str}")')
            
            email_count = len(data[0].split()) if data[0] else 0
            
            mail.close()
            mail.logout()
            
            # Wolt sends 2 semi-monthly payout reports
            status = "✅ OK" if email_count == 2 else "⚠️ WARNING"
            
            result = {
                "partner": "Wolt",
                "emails_found": email_count,
                "expected": 2,
                "status": status
            }
            
            if email_count == 0:
                self.issues.append(f"❌ Wolt: NO EMAILS found for {self.year}-{self.month:02d}")
                result["status"] = "❌ MISSING"
            elif email_count < 2:
                self.warnings.append(f"⚠️ Wolt: Only {email_count} emails found (expected 2)")
            
            return result
            
        except Exception as e:
            self.issues.append(f"❌ Wolt: Error checking emails: {e}")
            return {"partner": "Wolt", "error": str(e), "status": "❌ ERROR"}
    
    def generate_report(self) -> str:
        """Generate a comprehensive report"""
        uber = self.check_uber_eats()
        foodora = self.check_foodora()
        wolt = self.check_wolt()
        
        report = f"\n{'='*80}\n"
        report += f"INVOICE COMPLETENESS REPORT - {self.year}-{self.month:02d}\n"
        report += f"{'='*80}\n\n"
        
        # Summary table
        report += f"{'Partner':<20} {'Found':<10} {'Expected':<15} {'Status':<15}\n"
        report += f"{'-'*80}\n"
        
        for partner_data in [uber, foodora, wolt]:
            partner = partner_data.get('partner', 'Unknown')
            found = partner_data.get('emails_found', 0)
            
            if partner == "Uber Eats":
                expected = f"{partner_data.get('expected_min', 0)}-{partner_data.get('expected_max', 0)}"
            else:
                expected = str(partner_data.get('expected', 0))
            
            status = partner_data.get('status', '❓')
            report += f"{partner:<20} {found:<10} {expected:<15} {status:<15}\n"
        
        report += f"\n{'='*80}\n"
        
        # Issues
        if self.issues:
            report += f"\n🚨 CRITICAL ISSUES ({len(self.issues)}):\n"
            report += f"{'-'*80}\n"
            for issue in self.issues:
                report += f"{issue}\n"
        
        # Warnings
        if self.warnings:
            report += f"\n⚠️ WARNINGS ({len(self.warnings)}):\n"
            report += f"{'-'*80}\n"
            for warning in self.warnings:
                report += f"{warning}\n"
        
        # Recommendations
        if self.issues or self.warnings:
            report += f"\n💡 RECOMMENDED ACTIONS:\n"
            report += f"{'-'*80}\n"
            
            if any("Uber" in issue for issue in self.issues):
                report += "1. Check Uber Eats dashboard manually for missing payouts\n"
                report += "   URL: https://restaurant.uber.com\n"
                report += "   Create manual invoices for any missing weeks\n\n"
            
            if any("Foodora" in issue for issue in self.issues):
                report += "2. Contact Foodora support to resend missing invoices\n"
                report += "   Or download from Foodora partner portal\n\n"
            
            if any("Wolt" in issue for issue in self.issues):
                report += "3. Check Wolt partner portal for missing payout reports\n"
                report += "   URL: https://restaurant.wolt.com\n\n"
            
            report += "4. Run invoice generation after fixing issues:\n"
            report += f"   python generate_invoices.py {self.year} {self.month}\n"
        else:
            report += f"\n✅ ALL CHECKS PASSED - No issues found!\n"
        
        report += f"\n{'='*80}\n"
        
        return report

def check_month(year: int, month: int):
    """Check a specific month for invoice completeness"""
    checker = InvoiceChecker(year, month)
    report = checker.generate_report()
    print(report)
    
    # Save report to file
    report_dir = "./invoice_reports"
    os.makedirs(report_dir, exist_ok=True)
    report_file = f"{report_dir}/invoice_check_{year}_{month:02d}.txt"
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return len(checker.issues) == 0

def check_current_month():
    """Check the current month"""
    now = datetime.now()
    return check_month(now.year, now.month)

def check_last_month():
    """Check the previous month"""
    now = datetime.now()
    if now.month == 1:
        return check_month(now.year - 1, 12)
    else:
        return check_month(now.year, now.month - 1)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        check_month(year, month)
    elif len(sys.argv) == 2 and sys.argv[1] == "current":
        check_current_month()
    elif len(sys.argv) == 2 and sys.argv[1] == "last":
        check_last_month()
    else:
        print("Usage:")
        print("  python invoice_checker.py <year> <month>  # Check specific month")
        print("  python invoice_checker.py current          # Check current month")
        print("  python invoice_checker.py last             # Check last month")
        print("\nExample:")
        print("  python invoice_checker.py 2026 8          # Check August 2026")
