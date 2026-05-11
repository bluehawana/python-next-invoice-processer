import os
from typing import List, Optional, Dict
import stripe
from pydantic_settings import BaseSettings
import datetime

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

def _fmt_sek(val: float) -> str:
    """Format like Stripe dashboard: 423.07kr SEK"""
    return f"{val:,.2f}kr SEK"

async def generate_payout_reports(payout_ids: List[str]) -> List[str]:
    """
    Generates payout PDFs matching the Stripe dashboard layout exactly.
    Shows: header amount+date, Details panel, Summary table, Transactions table.
    Skips generation if PDF already exists locally.
    """
    downloaded_files = []
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)

    # Check which ones already exist - force regen if size looks wrong (old format)
    to_generate = []
    for pid in payout_ids:
        path = os.path.abspath(os.path.join(settings.INVOICE_STORAGE_PATH, f"stripe_payout_{pid}.pdf"))
        if os.path.exists(path) and os.path.getsize(path) > 20000:
            print(f"PDF already exists, skipping: {os.path.basename(path)}")
            downloaded_files.append(path)
        else:
            to_generate.append(pid)

    if not to_generate:
        return downloaded_files

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for pid in to_generate:
            try:
                print(f"Generating payout report for {pid}...")

                # Fetch payout
                payout = stripe.Payout.retrieve(pid)
                payout_amount = payout.amount / 100.0
                arrival_dt = datetime.datetime.fromtimestamp(payout.arrival_date)
                payout_date_long = arrival_dt.strftime("Completed %A, %B %-d")  # e.g. "Completed Tuesday, February 24"
                payout_date_short = arrival_dt.strftime("%b %-d")               # e.g. "Feb 24"

                # Fetch all balance transactions for this payout
                balance_txs = list(stripe.BalanceTransaction.list(payout=pid, limit=100).auto_paging_iter())

                # Build summary buckets: charges, refunds, adjustments
                buckets = {"charge": {"count": 0, "gross": 0.0, "fees": 0.0, "total": 0.0},
                           "refund":  {"count": 0, "gross": 0.0, "fees": 0.0, "total": 0.0},
                           "adjustment": {"count": 0, "gross": 0.0, "fees": 0.0, "total": 0.0}}

                # Build transaction rows
                tx_rows_html = ""
                for btx in balance_txs:
                    # Skip the payout entry itself - it's not a transaction
                    if btx.type == "payout":
                        continue

                    gross = btx.amount / 100.0
                    fee   = btx.fee / 100.0
                    net   = btx.net / 100.0
                    tx_type = btx.type  # charge / refund / payout / adjustment
                    desc = btx.description or ""
                    tx_date = datetime.datetime.fromtimestamp(btx.created).strftime("%b %-d")

                    # Enrich description from charge source
                    if btx.type == "charge" and btx.source:
                        try:
                            ch = stripe.Charge.retrieve(btx.source)
                            desc = ch.description or desc
                        except:
                            pass

                    # Bucket it
                    bucket_key = tx_type if tx_type in buckets else "adjustment"
                    buckets[bucket_key]["count"] += 1
                    buckets[bucket_key]["gross"] += gross
                    buckets[bucket_key]["fees"]  += fee
                    buckets[bucket_key]["total"] += net

                    # Fee display: show actual fee (negative) or blank if zero
                    fee_display = f"-{abs(fee):,.2f}kr" if fee != 0 else "0.00kr"
                    fee_color = "#e00" if fee != 0 else "#333"

                    tx_rows_html += f"""
                    <tr>
                        <td class="td">{tx_type.capitalize()}</td>
                        <td class="td amt">{gross:,.2f}kr SEK</td>
                        <td class="td amt" style="color:{fee_color};">{fee_display} SEK</td>
                        <td class="td amt bold">{net:,.2f}kr SEK</td>
                        <td class="td">{desc[:55]}</td>
                        <td class="td">{tx_date}</td>
                    </tr>"""

                # Summary totals
                ch  = buckets["charge"]
                ref = buckets["refund"]
                adj = buckets["adjustment"]
                payout_total = payout_amount

                # Fee display helper - show negative or zero
                def summary_fee(val):
                    return f"-{abs(val):,.2f}kr" if val != 0 else "0.00kr"

                html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
          font-size: 13px; color: #1a1a1a; background: #fff; padding: 32px; }}

  /* Top header */
  .top-label {{ color: #635bff; font-size: 13px; font-weight: 500; margin-bottom: 4px; }}
  .top-amount {{ font-size: 28px; font-weight: 700; margin-bottom: 2px; }}
  .badge-paid {{ display: inline-block; background: #d4edda; color: #155724;
                 font-size: 11px; font-weight: 600; padding: 2px 8px;
                 border-radius: 4px; margin-left: 8px; vertical-align: middle; }}
  .top-date {{ color: #555; font-size: 13px; margin-top: 4px; }}
  .site-tag {{ color: #635bff; font-size: 12px; font-weight: 600; margin-top: 6px; }}

  /* Two-column layout */
  .layout {{ display: flex; gap: 32px; margin-top: 24px; }}
  .main {{ flex: 1; }}
  .sidebar {{ width: 220px; flex-shrink: 0; }}

  /* Details panel */
  .panel {{ border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; }}
  .panel-title {{ font-weight: 700; font-size: 14px; margin-bottom: 12px; }}
  .detail-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 12px; }}
  .detail-label {{ color: #666; }}
  .detail-value {{ font-weight: 600; text-align: right; max-width: 130px; word-break: break-all; }}

  /* Summary table */
  .section-title {{ font-weight: 700; font-size: 14px; margin: 20px 0 10px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  .th {{ padding: 8px 10px; font-size: 11px; font-weight: 600; color: #666;
         border-bottom: 1px solid #e0e0e0; text-align: right; }}
  .th:first-child {{ text-align: left; }}
  .td {{ padding: 8px 10px; font-size: 12px; border-bottom: 1px solid #f0f0f0;
         vertical-align: top; text-align: right; }}
  .td:first-child {{ text-align: left; }}
  .amt {{ text-align: right; }}
  .bold {{ font-weight: 700; }}

  /* Summary footer row */
  .sum-row td {{ border-top: 2px solid #e0e0e0; border-bottom: none;
                 font-weight: 600; padding-top: 10px; }}
  .payout-row td {{ font-weight: 700; font-size: 13px; padding-top: 6px; border-bottom: none; }}
</style>
</head>
<body>

  <!-- Header -->
  <div class="top-label">Payouts</div>
  <div>
    <span class="top-amount">{payout_amount:,.2f}kr SEK</span>
    <span class="badge-paid">Paid</span>
  </div>
  <div class="top-date">{payout_date_long}</div>
  <div class="site-tag">🌐 ichiban.biz</div>

  <div class="layout">
    <!-- Main content -->
    <div class="main">

      <!-- Summary table -->
      <div class="section-title">Summary</div>
      <table>
        <thead>
          <tr>
            <th class="th" style="text-align:left;"></th>
            <th class="th">Count</th>
            <th class="th">Gross</th>
            <th class="th">Fees</th>
            <th class="th">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="td" style="text-align:left;">Charges</td>
            <td class="td">{ch['count']}</td>
            <td class="td">{ch['gross']:,.2f}kr</td>
            <td class="td" style="color:#e00;">{summary_fee(ch['fees'])}</td>
            <td class="td bold">{ch['total']:,.2f}kr</td>
          </tr>
          <tr>
            <td class="td" style="text-align:left;">Refunds</td>
            <td class="td">{ref['count']}</td>
            <td class="td">{ref['gross']:,.2f}kr</td>
            <td class="td">{summary_fee(ref['fees'])}</td>
            <td class="td bold">{ref['total']:,.2f}kr</td>
          </tr>
          <tr>
            <td class="td" style="text-align:left;">Adjustments</td>
            <td class="td">{adj['count']}</td>
            <td class="td">{adj['gross']:,.2f}kr</td>
            <td class="td">{summary_fee(adj['fees'])}</td>
            <td class="td bold">{adj['total']:,.2f}kr</td>
          </tr>
          <tr class="sum-row">
            <td colspan="3"></td>
            <td class="td" style="text-align:right; font-weight:700;">Payouts</td>
            <td class="td bold" style="font-size:14px;">{payout_total:,.2f}kr</td>
          </tr>
        </tbody>
      </table>

      <!-- Transactions table -->
      <div class="section-title" style="margin-top:28px;">Transactions</div>
      <table>
        <thead>
          <tr>
            <th class="th" style="text-align:left;">Type</th>
            <th class="th">Gross</th>
            <th class="th">Fee</th>
            <th class="th">Total</th>
            <th class="th" style="text-align:left;">Description</th>
            <th class="th">Date</th>
          </tr>
        </thead>
        <tbody>
          {tx_rows_html}
        </tbody>
      </table>

    </div>

    <!-- Sidebar: Details -->
    <div class="sidebar">
      <div class="panel">
        <div class="panel-title">Details</div>
        <div class="detail-row">
          <span class="detail-label">Payout completed</span>
          <span class="detail-value">{payout_date_short}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Payout ID</span>
          <span class="detail-value" style="font-size:10px;">{pid}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Internal note</span>
          <span class="detail-value">STRIPE PAYOUT</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Delivery method</span>
          <span class="detail-value">Standard</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Fee</span>
          <span class="detail-value">0.00kr</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Amount</span>
          <span class="detail-value bold" style="font-size:14px;">{payout_amount:,.2f}kr</span>
        </div>
      </div>
    </div>
  </div>

  <div style="margin-top:32px; border-top:1px solid #e0e0e0; padding-top:12px;
              font-size:11px; color:#999; text-align:center;">
    Hong Yan AB &bull; Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} &bull; Stripe API
  </div>

</body>
</html>"""

                filename = f"stripe_payout_{pid}.pdf"
                path = os.path.abspath(os.path.join(settings.INVOICE_STORAGE_PATH, filename))

                await page.set_content(html_content, wait_until="domcontentloaded")
                await page.pdf(path=path, format="A4", print_background=True,
                               margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"})

                print(f"Generated PDF: {path}")
                downloaded_files.append(path)

            except Exception as e:
                print(f"Error generating PDF for {pid}: {e}")
                import traceback
                traceback.print_exc()

        await browser.close()
    return downloaded_files

import asyncio

def download_stripe_invoices(year: int, month: int) -> List[str]:
    # ... placeholder
    return []
