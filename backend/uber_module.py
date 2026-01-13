"""
Uber Eats API Module - Fetch payment reports directly from Uber Eats API
"""
import requests
import os
from typing import List, Dict
from fpdf import FPDF
from stripe_module import settings

def get_uber_access_token() -> str:
    """
    Get OAuth2 access token from Uber using client credentials.
    """
    client_id = os.getenv("UBER_CLIENT_ID")
    client_secret = os.getenv("UBER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Uber credentials not set in .env")
        return None
    
    token_url = "https://login.uber.com/oauth/v2/token"
    
    try:
        response = requests.post(
            token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "eats.report"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Got Uber access token")
            return token_data.get("access_token")
        else:
            print(f"✗ Failed to get Uber token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error getting Uber token: {e}")
        return None

def fetch_uber_payments(year: int, month: int) -> List[Dict]:
    """
    Fetch payment reports from Uber Eats API for the given month.
    """
    access_token = get_uber_access_token()
    if not access_token:
        return []
    
    # Calculate date range
    import datetime
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, month + 1, 1)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Try the Uber Eats Reporting API
    # Note: The exact endpoint may vary - this is based on their documentation
    reports_url = "https://api.uber.com/v1/eats/stores/reports/payments"
    
    try:
        response = requests.get(
            reports_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            params={
                "start_date": start_str,
                "end_date": end_str
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Got Uber payments: {len(data.get('payments', []))} records")
            return data.get("payments", [])
        else:
            print(f"✗ Uber API error: {response.status_code} - {response.text[:200]}")
            return []
    except Exception as e:
        print(f"✗ Error fetching Uber payments: {e}")
        return []

def generate_uber_invoice_pdf(payment: Dict, filepath: str) -> str:
    """
    Generate a PDF invoice from Uber payment data.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "UBER EATS", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Ichiban Sushi", ln=True)
    pdf.ln(5)
    
    # Payment details
    pdf.set_font("Arial", "B", 12)
    period = payment.get("period", "Unknown Period")
    pdf.cell(0, 10, f"Betalningsöversikt: {period}", ln=True)
    pdf.ln(5)
    
    # Amount
    pdf.set_font("Arial", size=11)
    amount = payment.get("amount", 0)
    currency = payment.get("currency", "SEK")
    pdf.cell(0, 8, f"Total Betalning: {amount:,.2f} {currency}", ln=True)
    
    # Breakdown if available
    if "breakdown" in payment:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "Betalningsberäkning:", ln=True)
        pdf.set_font("Arial", size=10)
        for item in payment.get("breakdown", []):
            pdf.cell(0, 6, f"  {item.get('label', '')}: {item.get('value', '')}", ln=True)
    
    pdf.output(filepath)
    return filepath

def download_uber_invoices(year: int, month: int) -> List[str]:
    """
    Main function to download Uber Eats payment invoices for the month.
    """
    payments = fetch_uber_payments(year, month)
    
    if not payments:
        print("No Uber payments found via API, falling back to email method")
        return []
    
    downloaded = []
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)
    
    for i, payment in enumerate(payments):
        filename = f"ubereats_payment_{year}_{month:02d}_{i+1}.pdf"
        filepath = os.path.join(settings.INVOICE_STORAGE_PATH, filename)
        generate_uber_invoice_pdf(payment, filepath)
        downloaded.append(os.path.abspath(filepath))
        print(f"Generated Uber invoice: {filename}")
    
    return downloaded

if __name__ == "__main__":
    # Test the module
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Testing Uber Eats API connection...")
    token = get_uber_access_token()
    if token:
        print(f"Token (first 20 chars): {token[:20]}...")
        invoices = download_uber_invoices(2025, 12)
        print(f"Downloaded {len(invoices)} invoices")
