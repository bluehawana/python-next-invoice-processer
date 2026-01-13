import os
import asyncio
from typing import List
from playwright.async_api import async_playwright
from stripe_module import settings

async def scrape_wolt_invoices(year: int, month: int) -> List[str]:
    """
    Scrapes Wolt Merchant Portal for payout reports.
    Needs WOLT_USER and WOLT_PASS in .env.
    """
    if not settings.WOLT_USER or not settings.WOLT_PASS:
        print("Wolt credentials not set. Skipping portal scrape.")
        return []

    downloaded_files = []
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Headful for manual intervention if needed
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to Wolt Merchant Portal...")
        await page.goto("https://merchant.wolt.com/login")
        
        # User login
        # await page.fill('input[name="email"]', settings.WOLT_USER)
        # await page.fill('input[name="password"]', settings.WOLT_PASS)
        # await page.click('button[type="submit"]')
        
        print("Please log in to Wolt and navigate to 'Utbetalningsrapport'...")
        
        try:
            # Wait for dashboard or specific report page
            await page.wait_for_url("**/payouts**", timeout=60000)
            print("Wolt Payouts page detected.")
            
            # Implementation logic for clicking 'Download' would go here
            # For now, it's a foundation for the user to use.
            
        except Exception as e:
            print(f"Wolt portal wait failed: {e}")

        await browser.close()
    
    return downloaded_files
