#!/usr/bin/env python3
"""
Scrape Uber Eats Merchant portal using your existing Chrome session.
No login needed — uses your already logged-in Chrome profile.
"""
import asyncio
import os
import subprocess
import time
from playwright.async_api import async_playwright
from email_module import create_email_pdf
from stripe_module import settings

PAGES = [
    {
        "url": "https://merchants.ubereats.com/manager/payments?restaurantUUID=d634d007-26a8-46d5-b19d-de90a4bad3d1&start=2026-05-11&end=2026-05-17&rangeType=0&settlement=4f7e06a8-ba44-5c47-8dc0-732ae11b49b6",
        "period": "5/11/26–5/17/26",
        "filename": "ubereats_scraped_5_11_5_17_email_body.pdf",
    },
    {
        "url": "https://merchants.ubereats.com/manager/payments?restaurantUUID=d634d007-26a8-46d5-b19d-de90a4bad3d1&start=2026-05-04&end=2026-05-10&rangeType=0&settlement=181c9890-e001-5882-b371-c345eed1624e",
        "period": "5/4/26–5/10/26",
        "filename": "ubereats_scraped_5_04_5_10_email_body.pdf",
    },
]

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REMOTE_PORT = 9222
# Your Chrome user data (uses your existing Google login session)
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")


async def scrape_page(page, info):
    print(f"\n→ Loading {info['period']}...")
    await page.goto(info["url"], wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(4000)
    text = await page.inner_text("body")

    if "Total utbetalning" in text or "Intäkter" in text or "Betalningsspecifikation" in text:
        print(f"  ✅ Real payment data found ({len(text)} chars)")
        print(f"  Preview: {text[:300]}")
    else:
        print(f"  ⚠️  No payment data found. Preview:\n  {text[:300]}")

    subject = f"Uber Eats-betalningssammanfattning för Ichiban Sushi {info['period']}"
    out_path = os.path.join(settings.INVOICE_STORAGE_PATH, info["filename"])
    create_email_pdf(subject, text, out_path, "ubereats")
    print(f"  PDF saved: {info['filename']}")
    return out_path, text


async def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices", "may-2026")
    os.makedirs(output_dir, exist_ok=True)
    settings.INVOICE_STORAGE_PATH = output_dir

    # Launch Chrome with remote debugging using your existing profile
    print("Launching Chrome with your existing session...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={REMOTE_PORT}",
        f"--user-data-dir={CHROME_USER_DATA}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(3)  # wait for Chrome to start

    async with async_playwright() as p:
        # Connect to the running Chrome instance
        browser = await p.chromium.connect_over_cdp(f"http://localhost:{REMOTE_PORT}")
        print(f"Connected to Chrome. Contexts: {len(browser.contexts)}")

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()

        results = []
        for info in PAGES:
            path, text = await scrape_page(page, info)
            results.append((path, text))

        await page.close()

    chrome_proc.terminate()

    # Summary
    print(f"\n{'='*55}")
    all_ok = True
    for path, text in results:
        fname = os.path.basename(path)
        has_data = "Total utbetalning" in text or "Intäkter" in text
        status = "✅ REAL DATA" if has_data else "❌ NO DATA"
        if not has_data:
            all_ok = False
        print(f"{status} → {fname}")
    print("="*55)

    if all_ok:
        from print_module import print_pdf
        for path, _ in results:
            print(f"Printing {os.path.basename(path)}...")
            print_pdf(path)
        print("✅ All printed!")
    else:
        print("⚠️  Some PDFs have no real data — not printing.")
        print("   Make sure you are logged into Uber Eats in Chrome.")


if __name__ == "__main__":
    asyncio.run(main())
