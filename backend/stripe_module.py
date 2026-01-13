import os
from typing import List, Optional, Dict
import stripe
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    STRIPE_API_KEY: str = ""
    FOODORA_USER: str = ""
    FOODORA_PASS: str = ""
    UBER_USER: str = ""
    UBER_PASS: str = ""
    WOLT_USER: str = ""
    WOLT_PASS: str = ""
    EMAIL_HOST: str = ""
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""
    PRINTER_NAME: str = ""
    INVOICE_STORAGE_PATH: str = "./invoices"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        extra = "ignore" # Allow other env vars

settings = Settings()

if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

def download_stripe_payouts(year: int, month: int) -> List[Dict]:
    """
    Lists Stripe payouts for a specific month.
    """
    if not stripe.api_key:
        print("Stripe API key not set in .env.")
        return []

    import datetime
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)

    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())

    try:
        print(f"Fetching Stripe payouts for {year}-{month:02d}...")
        payouts = stripe.Payout.list(
            arrival_date={
                "gte": start_ts,
                "lt": end_ts
            },
            limit=100
        )
        
        results = []
        for p in payouts.auto_paging_iter():
            results.append({
                "id": p.id,
                "amount": p.amount / 100.0, # Stripe uses subunits
                "currency": p.currency.upper(),
                "arrival_date": datetime.datetime.fromtimestamp(p.arrival_date).strftime('%Y-%m-%d'),
                "status": p.status,
                # Note: Stripe API doesn't provide a direct PDF for payouts easily.
                # Usually requires pulling Balance Transactions or using the Dashboard URL.
                "report_url": f"https://dashboard.stripe.com/payouts/{p.id}"
            })
        
        return results
    except Exception as e:
        print(f"Error fetching Stripe payouts: {e}")
        return []

from playwright.async_api import async_playwright

async def generate_payout_reports(payout_ids: List[str]) -> List[str]:
    """
    100% Automated: Fetches payout details via Stripe API and generates professional PDFs.
    No dashboard login required.
    """
    downloaded_files = []
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for pid in payout_ids:
            try:
                print(f"Generating automated report for payout {pid}...")
                
                # 1. Fetch Payout Details
                payout = stripe.Payout.retrieve(pid)
                
                # 2. Fetch Balance Transactions (Charges, Fees, etc.)
                transactions = stripe.BalanceTransaction.list(payout=pid, limit=100)
                
                # aggregate data
                tx_list_html = ""
                summary_data = {"charge": {"gross": 0, "fee": 0}, "refund": {"gross": 0, "fee": 0}, "adjustment": {"gross": 0, "fee": 0}}
                
                for tx in transactions.auto_paging_iter():
                    amount_sek = tx.amount / 100.0
                    fee_sek = tx.fee / 100.0
                    net_sek = tx.net / 100.0
                    
                    tx_list_html += f"""
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{tx.type.capitalize()}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{amount_sek:,.2f} kr</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{fee_sek:,.2f} kr</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{net_sek:,.2f} kr</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-size: 10px; color: #666;">{tx.description or pid}</td>
                    </tr>
                    """
                    
                    if tx.type in summary_data:
                        summary_data[tx.type]["gross"] += amount_sek
                        summary_data[tx.type]["fee"] += fee_sek

                html_content = f"""
                <html>
                <body style="font-family: -apple-system, sans-serif; padding: 40px; color: #333;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #635bff; padding-bottom: 20px; margin-bottom: 30px;">
                        <div>
                            <h1 style="margin: 0; color: #635bff;">Payout Summary</h1>
                            <p style="margin: 5px 0; color: #666;">ID: {pid}</p>
                        </div>
                        <div style="text-align: right;">
                            <h2 style="margin: 0;">{payout.amount/100.0:,.2f} kr SEK</h2>
                            <p style="margin: 5px 0; background: #e3ffeb; color: #0d9633; padding: 2px 8px; border-radius: 4px; display: inline-block;">Paid</p>
                        </div>
                    </div>

                    <h3>Summary</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <tr style="background: #f8f9fb; font-weight: bold;">
                            <td style="padding: 10px;">Type</td>
                            <td style="padding: 10px;">Gross</td>
                            <td style="padding: 10px;">Fees</td>
                            <td style="padding: 10px;">Total</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">Charges</td>
                            <td style="padding: 10px;">{summary_data['charge']['gross']:,.2f} kr</td>
                            <td style="padding: 10px;">{summary_data['charge']['fee']:,.2f} kr</td>
                            <td style="padding: 10px;">{(summary_data['charge']['gross'] + summary_data['charge']['fee']):,.2f} kr</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">Refunds</td>
                            <td style="padding: 10px;">{summary_data['refund']['gross']:,.2f} kr</td>
                            <td style="padding: 10px;">{summary_data['refund']['fee']:,.2f} kr</td>
                            <td style="padding: 10px;">{(summary_data['refund']['gross'] + summary_data['refund']['fee']):,.2f} kr</td>
                        </tr>
                    </table>

                    <h3>Transactions</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr style="background: #f8f9fb; font-weight: bold;">
                            <td style="padding: 10px;">Type</td>
                            <td style="padding: 10px;">Gross</td>
                            <td style="padding: 10px;">Fee</td>
                            <td style="padding: 10px;">Total</td>
                            <td style="padding: 10px;">Description</td>
                        </tr>
                        {tx_list_html}
                    </table>
                </body>
                </html>
                """
                
                filename = f"stripe_payout_{pid}.pdf"
                path = os.path.abspath(os.path.join(settings.INVOICE_STORAGE_PATH, filename))
                
                await page.set_content(html_content)
                await page.pdf(path=path, format="A4", print_background=True)
                
                print(f"Generated automated PDF: {path}")
                downloaded_files.append(path)
                
            except Exception as e:
                print(f"Error generating PDF for {pid}: {e}")
                
        await browser.close()
    return downloaded_files

import asyncio

def download_stripe_invoices(year: int, month: int) -> List[str]:
    # ... placeholder
    return []
