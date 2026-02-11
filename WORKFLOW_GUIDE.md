# Invoice Processing System - Workflow Guide

## 🎉 System Status: OPERATIONAL

Your invoice processing system is now live at **invoices.bluehawana.com** and fully functional!

## 📋 What's Working

### ✅ Automated Invoice Collection
- **Stripe**: Automatically fetches payouts via API and generates PDF reports
- **Wolt**: Collects invoices from email (IMAP)
- **Uber Eats**: Collects payment summaries from email and formats them
- **Foodora**: Email collection configured (awaiting invoices)

### ✅ Storage & Processing
- **R2 Cloud Storage**: Files automatically uploaded to Cloudflare R2
- **Local Backup**: Files stored in `backend/invoices/` before upload
- **Reconciliation**: Matches collected invoices with handwritten records

### ✅ API Endpoints
- `GET /` - Health check
- `POST /trigger-download?year=2025&month=1` - Trigger invoice collection
- `GET /reconciliation-status` - View collection results
- `POST /upload-paper` - Upload handwritten invoice image for OCR
- `POST /print-file` - Print a specific invoice
- `POST /print-batch` - Batch print multiple invoices
- `GET /view-file?path=...` - View/download invoice files

## 🚀 Quick Start

### 1. Start the Backend (Local Development)

```bash
cd backend
source venv/bin/activate
python3 main.py
```

Or use the convenience script:
```bash
cd backend
./start_server.sh
```

The API will be available at `http://localhost:8000`

### 2. Collect Invoices for a Month

**Via API:**
```bash
curl -X POST "http://localhost:8000/trigger-download?year=2025&month=1"
```

**Via Python:**
```python
import requests
response = requests.post("http://localhost:8000/trigger-download?year=2025&month=1")
print(response.json())
```

### 3. Check Results

```bash
curl "http://localhost:8000/reconciliation-status" | python3 -m json.tool
```

## 🧪 Testing

### Test Complete Workflow
```bash
cd backend
source venv/bin/activate
python3 test_full_workflow.py
```

This will:
1. Collect Stripe payouts
2. Generate Stripe PDF reports
3. Fetch email invoices (Wolt, Uber, Foodora)
4. Reconcile all invoices
5. Test R2 upload

### Test API Endpoints
```bash
cd backend
source venv/bin/activate
python3 test_api.py
```

### Test System Components
```bash
cd backend
source venv/bin/activate
python3 test_workflow.py
```

Tests:
- Environment variables
- Stripe API connection
- Email (IMAP) connection
- R2 storage connection
- Invoice collection

## 📊 January 2025 Results

Based on the latest test run:

| Partner | Files Collected | Status |
|---------|----------------|--------|
| Stripe | 15 payouts (10,644.85 SEK) | ✅ Working |
| Wolt | 9 invoices | ✅ Working |
| Uber Eats | 1 summary | ✅ Working |
| Foodora | 0 (no emails found) | ⚠️ Awaiting invoices |

## 🔧 Configuration

All configuration is in `backend/.env`:

```env
# Stripe API
STRIPE_API_KEY=sk_live_...

# Email (Gmail IMAP)
EMAIL_HOST=imap.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Uber Eats API
UBER_CLIENT_ID=...
UBER_CLIENT_SECRET=...

# R2 Storage (Cloudflare)
R2_ENDPOINT_URL=https://...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=invoicehandlingsys

# Storage Path
INVOICE_STORAGE_PATH=./invoices
```

## 📁 File Organization

Invoices are automatically named with a prefix for easy identification:

- `stripe_payout_po_*.pdf` - Stripe payout reports
- `wolt_*_*.pdf` - Wolt invoices
- `ubereats_*_email_body.pdf` - Uber Eats summaries
- `foodora_*_*.pdf` - Foodora invoices

## 🔄 Workflow Details

### Automatic Collection Process

1. **Stripe Payouts**
   - Fetches payout data via Stripe API
   - Generates detailed PDF reports with transaction breakdown
   - Includes fees, refunds, and net amounts

2. **Email Invoices**
   - Connects to Gmail via IMAP
   - Searches for emails from Wolt, Uber Eats, and Foodora
   - Downloads PDF attachments
   - For emails without attachments (like Uber), generates formatted PDFs from email body

3. **R2 Upload**
   - Uploads all collected files to Cloudflare R2
   - Deletes local copies after successful upload
   - Generates presigned URLs for viewing

4. **Reconciliation**
   - Matches collected invoices with handwritten records
   - Identifies missing or unmatched invoices
   - Provides status for each partner

## 🐛 Troubleshooting

### Backend Not Collecting Invoices

**Check if venv is activated:**
```bash
cd backend
source venv/bin/activate
python3 test_workflow.py
```

**Common Issues:**
- Missing dependencies: Run `pip install -r requirements.txt`
- Wrong Python version: Ensure Python 3.9+
- Environment variables not loaded: Check `.env` file exists

### Email Collection Issues

**Gmail App Password:**
- Don't use your regular Gmail password
- Generate an App Password: Google Account → Security → 2-Step Verification → App Passwords

**Date Range:**
- The system searches from the 1st of the month to 15 days after month end
- This catches late-arriving invoices (e.g., Uber sends weekly summaries)

### R2 Upload Failures

**Check credentials:**
```bash
cd backend
source venv/bin/activate
python3 -c "from r2_module import get_r2_client; print('✅ OK' if get_r2_client() else '❌ Failed')"
```

## 🚀 Deployment

The system is deployed on RackNerd VPS:

**Backend:** `invoices-api.bluehawana.com` (systemd service)
**Frontend:** `invoices.bluehawana.com` (Cloudflare Pages)

### Deploy Backend Updates

```bash
./deployment/deploy_backend.sh
```

This will:
1. Sync files to server
2. Install dependencies in venv
3. Restart systemd service
4. Update nginx configuration

### Check Service Status

```bash
ssh racknerd "sudo systemctl status invoice-backend"
```

### View Logs

```bash
ssh racknerd "sudo journalctl -u invoice-backend -f"
```

## 📝 Next Steps

### Recommended Improvements

1. **Frontend Integration**
   - Connect frontend to API endpoints
   - Display reconciliation results
   - Add manual invoice upload UI

2. **OCR Enhancement**
   - Integrate Vision AI (Google Gemini/OpenAI GPT-4V)
   - Automatically extract amounts from handwritten images
   - Currently uses mock data

3. **Foodora Integration**
   - Add Foodora portal scraping (requires 2FA handling)
   - Or wait for email invoices

4. **Automated Scheduling**
   - Add cron job to run collection monthly
   - Send email notifications when complete

5. **Bankgiro Integration**
   - Uncomment bankgiro code in `main.py`
   - Add SEB API integration

## 🎯 Usage Examples

### Collect Last Month's Invoices

```python
import requests
from datetime import datetime, timedelta

# Get last month
today = datetime.now()
last_month = today.replace(day=1) - timedelta(days=1)

response = requests.post(
    "http://localhost:8000/trigger-download",
    params={"year": last_month.year, "month": last_month.month}
)
print(response.json())
```

### Upload Handwritten Invoice Image

```python
import requests

with open("invoice_photo.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload-paper",
        files={"file": f}
    )
print(response.json())
```

### Print All Invoices for a Partner

```python
import requests

# Get reconciliation status
status = requests.get("http://localhost:8000/reconciliation-status").json()

# Find Wolt invoices
for record in status['records']:
    if record['partner'].lower() == 'wolt':
        files = record['files']
        
        # Print all
        response = requests.post(
            "http://localhost:8000/print-batch",
            json=files
        )
        print(f"Printed {len(files)} Wolt invoices")
```

## 📞 Support

For issues or questions:
1. Check logs: `sudo journalctl -u invoice-backend -f`
2. Run diagnostic: `python3 test_workflow.py`
3. Verify environment: Check `.env` file

---

**System Version:** 1.0  
**Last Updated:** February 2025  
**Status:** ✅ Production Ready
