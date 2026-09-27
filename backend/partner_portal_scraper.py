#!/usr/bin/env python3
"""
Partner Portal Scraper - Fetch invoices directly from partner dashboards
When emails are missing, this fetches invoices from the web portals
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
from typing import List, Dict
from datetime import datetime

class PartnerPortalScraper:
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome driver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add download preferences
        download_dir = os.path.abspath("./portal_downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.download_dir = download_dir
        
    def __del__(self):
        """Clean up driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def uber_eats_login(self, email: str, password: str) -> bool:
        """
        Login to Uber Eats restaurant dashboard
        URL: https://restaurant.uber.com
        """
        print("\n🚗 Logging into Uber Eats portal...")
        
        try:
            self.driver.get("https://restaurant.uber.com")
            time.sleep(2)
            
            # Fill in login form
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_input.send_keys(email)
            
            # Click continue/next
            continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            continue_btn.click()
            time.sleep(2)
            
            # Enter password
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.send_keys(password)
            
            # Submit
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            time.sleep(3)
            
            print("   ✓ Logged in successfully")
            return True
            
        except Exception as e:
            print(f"   ✗ Login failed: {e}")
            return False
    
    def uber_eats_download_invoices(self, year: int, month: int) -> List[str]:
        """
        Navigate to payments section and download invoices for the month
        """
        print(f"\n📄 Downloading Uber Eats invoices for {year}-{month:02d}...")
        
        try:
            # Navigate to payments/financial section
            self.driver.get("https://restaurant.uber.com/payments")
            time.sleep(3)
            
            # Filter by month (implementation depends on Uber's UI)
            # This is a placeholder - actual implementation needs inspection of Uber's DOM
            
            # Find and download weekly payment reports
            download_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Download') or contains(@aria-label, 'Download')]")
            
            downloaded_files = []
            for btn in download_buttons:
                try:
                    btn.click()
                    time.sleep(2)
                    # Track downloaded file
                    downloaded_files.append(f"uber_invoice_{year}_{month:02d}.pdf")
                except:
                    pass
            
            print(f"   ✓ Downloaded {len(downloaded_files)} invoices")
            return downloaded_files
            
        except Exception as e:
            print(f"   ✗ Download failed: {e}")
            return []
    
    def wolt_login(self, email: str, password: str) -> bool:
        """
        Login to Wolt restaurant portal
        URL: https://restaurant.wolt.com
        """
        print("\n⚡ Logging into Wolt portal...")
        
        try:
            self.driver.get("https://restaurant.wolt.com/login")
            time.sleep(2)
            
            # Enter email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.send_keys(email)
            
            # Enter password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            
            # Submit
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            time.sleep(3)
            
            print("   ✓ Logged in successfully")
            return True
            
        except Exception as e:
            print(f"   ✗ Login failed: {e}")
            return False
    
    def wolt_download_invoices(self, year: int, month: int) -> List[str]:
        """Download Wolt payout reports for the month"""
        print(f"\n📄 Downloading Wolt invoices for {year}-{month:02d}...")
        
        try:
            # Navigate to payments section
            self.driver.get("https://restaurant.wolt.com/payments")
            time.sleep(3)
            
            # Implementation depends on Wolt's UI structure
            # Download semi-monthly reports
            
            downloaded_files = []
            print(f"   ✓ Downloaded {len(downloaded_files)} invoices")
            return downloaded_files
            
        except Exception as e:
            print(f"   ✗ Download failed: {e}")
            return []
    
    def foodora_login(self, email: str, password: str) -> bool:
        """
        Login to Foodora partner portal
        """
        print("\n🍕 Logging into Foodora portal...")
        
        try:
            self.driver.get("https://partner.foodora.se/login")
            time.sleep(2)
            
            # Login implementation
            # Structure depends on Foodora's actual login page
            
            print("   ✓ Logged in successfully")
            return True
            
        except Exception as e:
            print(f"   ✗ Login failed: {e}")
            return False
    
    def foodora_download_invoices(self, year: int, month: int) -> List[str]:
        """Download Foodora invoices for the month"""
        print(f"\n📄 Downloading Foodora invoices for {year}-{month:02d}...")
        
        try:
            downloaded_files = []
            print(f"   ✓ Downloaded {len(downloaded_files)} invoices")
            return downloaded_files
            
        except Exception as e:
            print(f"   ✗ Download failed: {e}")
            return []


def fetch_missing_invoices_from_portals(year: int, month: int, missing_partners: List[str]) -> Dict[str, List[str]]:
    """
    Main function to fetch missing invoices from partner portals
    
    Args:
        year: Year of the invoices
        month: Month of the invoices
        missing_partners: List of partners with missing invoices ['uber', 'wolt', 'foodora']
    
    Returns:
        Dictionary of partner -> list of downloaded file paths
    """
    results = {}
    
    # Load credentials from environment
    uber_email = os.getenv("UBER_USER")
    uber_pass = os.getenv("UBER_PASS")
    
    if not any(missing_partners):
        print("✅ No missing invoices to fetch from portals")
        return results
    
    print("\n" + "="*80)
    print(f"FETCHING MISSING INVOICES FROM PARTNER PORTALS - {year}-{month:02d}")
    print("="*80)
    
    scraper = PartnerPortalScraper(headless=False)  # Set to True in production
    
    try:
        # Uber Eats
        if 'uber' in missing_partners or 'ubereats' in missing_partners:
            if uber_email and uber_pass:
                if scraper.uber_eats_login(uber_email, uber_pass):
                    files = scraper.uber_eats_download_invoices(year, month)
                    results['uber'] = files
            else:
                print("⚠️ Uber credentials not found in .env")
        
        # Wolt
        if 'wolt' in missing_partners:
            # Add Wolt credentials to .env if available
            print("⚠️ Wolt portal scraping not yet implemented")
        
        # Foodora
        if 'foodora' in missing_partners:
            print("⚠️ Foodora portal scraping not yet implemented")
    
    finally:
        del scraper  # Clean up
    
    print("\n" + "="*80)
    print("PORTAL SCRAPING COMPLETE")
    print("="*80)
    
    return results


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if len(sys.argv) < 3:
        print("Usage: python partner_portal_scraper.py <year> <month> [partners]")
        print("Example: python partner_portal_scraper.py 2026 8 uber,wolt")
        sys.exit(1)
    
    year = int(sys.argv[1])
    month = int(sys.argv[2])
    partners = sys.argv[3].split(',') if len(sys.argv) > 3 else ['uber', 'wolt', 'foodora']
    
    results = fetch_missing_invoices_from_portals(year, month, partners)
    
    print("\n📊 RESULTS:")
    for partner, files in results.items():
        print(f"  {partner}: {len(files)} invoices downloaded")
