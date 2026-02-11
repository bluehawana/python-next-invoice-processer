# 🧾 Invoice Management System

> Automated invoice collection, reconciliation, and management system for Ichiban Sushi

[![Status](https://img.shields.io/badge/status-production-success)](https://invoices.bluehawana.com)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](https://invoices-api.bluehawana.com)
[![Frontend](https://img.shields.io/badge/frontend-Next.js-000000)](https://invoices.bluehawana.com)

## 🌟 Features

### Automated Collection
- **Stripe**: API-based payout fetching with detailed PDF reports
- **Wolt**: Email-based invoice collection via IMAP
- **Uber Eats**: HTML email parsing with formatted PDF generation
- **Foodora**: Email invoice collection (configured)

### Smart Processing
- **OCR**: Handwritten invoice recognition (ready for AI integration)
- **Reconciliation**: Automatic matching of digital invoices with records
- **Cloud Storage**: Cloudflare R2 integration for secure file storage
- **Batch Operations**: Print multiple invoices at once

### Modern Interface
- **Dark Theme**: Professional design matching BlueHawana brand
- **Real-time Status**: Live partner connection monitoring
- **Responsive**: Works on desktop, tablet, and mobile
- **Drag & Drop**: Easy file uploads

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Frontend (Next.js)                 │
│  invoices.bluehawana.com            │
│  - React UI                         │
│  - Static Export                    │
│  - Cloudflare Pages                 │
└──────────────┬──────────────────────┘
               │ HTTPS API Calls
               ▼
┌─────────────────────────────────────┐
│  Backend (FastAPI)                  │
│  invoices-api.bluehawana.com        │
│  - Python 3.9+                      │
│  - Invoice Processing               │
│  - Email Integration                │
│  - Stripe API                       │
└──────────────┬──────────────────────┘
               │
               ├─► Stripe API
               ├─► Gmail IMAP
               ├─► Cloudflare R2
               └─► Local Storage
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Gmail account with App Password
- Stripe API key
- Cloudflare R2 account (optional)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start server
python main.py
# Or use: ./start_server.sh
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 📋 Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Stripe
STRIPE_API_KEY=sk_live_...

# Email (Gmail)
EMAIL_HOST=imap.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Uber Eats API
UBER_CLIENT_ID=...
UBER_CLIENT_SECRET=...

# Cloudflare R2
R2_ENDPOINT_URL=https://...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=invoicehandlingsys

# Storage
INVOICE_STORAGE_PATH=./invoices
```

### Frontend Environment Variables

Create `frontend/.env.local`:

```env
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (set in Vercel)
# NEXT_PUBLIC_API_URL=https://invoices-api.bluehawana.com
```

## 🧪 Testing

### Test Complete Workflow

```bash
cd backend
source venv/bin/activate
python test_full_workflow.py
```

This tests:
- Stripe API connection
- Email collection
- PDF generation
- R2 upload
- Reconciliation

### Test Individual Components

```bash
# Test environment and connections
python test_workflow.py

# Test API endpoints
python test_api.py
```

### System Status Check

```bash
# From project root
./check_system.sh
```

## 📦 Deployment

### Backend (VPS)

```bash
# Deploy to production server
./deployment/deploy_backend.sh
```

This will:
1. Sync files to server
2. Install dependencies in venv
3. Configure systemd service
4. Setup nginx reverse proxy
5. Obtain SSL certificate

### Frontend (Cloudflare Pages)

Already deployed! Just push changes:

```bash
# Commit and push
git add .
git commit -m "Update invoice system"
git push origin main

# Cloudflare Pages deploys automatically!
```

Or deploy manually:
```bash
./deploy_frontend.sh
```

See [CLOUDFLARE_DEPLOYMENT.md](CLOUDFLARE_DEPLOYMENT.md) for detailed instructions.

## 📖 Usage

### Collect Invoices

**Via UI:**
1. Open https://invoices.bluehawana.com
2. Click "Sync Invoices"
3. Wait for collection to complete
4. View results in reconciliation table

**Via API:**
```bash
curl -X POST "https://invoices-api.bluehawana.com/trigger-download?year=2025&month=1"
```

**Via Python:**
```python
import requests

response = requests.post(
    "https://invoices-api.bluehawana.com/trigger-download",
    params={"year": 2025, "month": 1}
)
print(response.json())
```

### Upload Handwritten Records

1. Take a photo of handwritten invoice records
2. Click "Upload" in the UI
3. Select image file (PNG, JPG, HEIC)
4. System will process with OCR
5. Results appear in reconciliation table

### Print Invoices

**Single file:**
- Click "View" button next to invoice
- Use browser print function

**Batch print:**
1. Check boxes next to invoices
2. Click "Print Selected"
3. Or click "Print All" for a partner

## 🎨 Design System

The interface uses a professional dark theme matching www.bluehawana.com:

### Colors
- **Background**: Slate-950 with gradient
- **Cards**: Slate-800/40 with backdrop blur
- **Accents**: Blue (#3b82f6) and Cyan (#06b6d4)
- **Success**: Green-400
- **Warning**: Amber-400

### Typography
- **Font**: Geist Sans (Next.js default)
- **Headings**: Bold, gradient text
- **Body**: Slate-300/400

### Components
- Glass-morphism cards
- Animated status indicators
- Smooth transitions
- Custom scrollbar
- Responsive grid layout

## 📊 API Endpoints

### GET /
Health check

### POST /trigger-download
Trigger invoice collection
- **Params**: `year`, `month`
- **Returns**: `{"message": "Sync started"}`

### GET /reconciliation-status
Get reconciliation results
- **Returns**: Partner status and matched files

### POST /upload-paper
Upload handwritten invoice image
- **Body**: multipart/form-data with file
- **Returns**: OCR results

### POST /print-file
Print single invoice
- **Params**: `file_path`

### POST /print-batch
Print multiple invoices
- **Body**: JSON array of file paths

### GET /view-file
View/download invoice
- **Params**: `path` (local or R2 URI)
- **Returns**: Redirect to file or presigned URL

## 🔧 Troubleshooting

### Backend Issues

**Dependencies missing:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Service not running:**
```bash
# Check status
ssh racknerd "sudo systemctl status invoice-backend"

# View logs
ssh racknerd "sudo journalctl -u invoice-backend -f"

# Restart
ssh racknerd "sudo systemctl restart invoice-backend"
```

### Frontend Issues

**Build fails:**
```bash
cd frontend
rm -rf .next out node_modules
npm install
npm run build
```

**API connection fails:**
- Check CORS settings in `backend/main.py`
- Verify `NEXT_PUBLIC_API_URL` is correct
- Test API: `curl https://invoices-api.bluehawana.com/`

### Email Collection Issues

**Gmail authentication:**
1. Enable 2-Step Verification
2. Generate App Password
3. Use App Password in `.env`, not regular password

**No invoices found:**
- Check date range (searches 1st to 15 days after month end)
- Verify email subjects match patterns
- Check spam folder

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── stripe_module.py        # Stripe integration
│   ├── email_module.py         # Email collection
│   ├── uber_module.py          # Uber Eats API
│   ├── wolt_module.py          # Wolt scraping
│   ├── foodora_module.py       # Foodora scraping
│   ├── ocr_module.py           # OCR processing
│   ├── r2_module.py            # R2 storage
│   ├── print_module.py         # Printing
│   ├── bankgiro_module.py      # Bankgiro (future)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Configuration
│   └── invoices/               # Local storage
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Main UI
│   │   ├── layout.tsx          # Layout
│   │   └── globals.css         # Styles
│   ├── package.json            # Node dependencies
│   ├── next.config.ts          # Next.js config
│   └── .env.local              # Local config
│
├── deployment/
│   ├── deploy_backend.sh       # Backend deployment
│   ├── backend.service         # Systemd service
│   └── nginx-backend.conf      # Nginx config
│
├── check_system.sh             # System status check
├── fix_production.sh           # Production fixes
├── deploy_frontend.sh          # Frontend deployment
├── WORKFLOW_GUIDE.md           # Detailed workflow
├── VERCEL_DEPLOYMENT.md        # Vercel guide
└── README.md                   # This file
```

## 🤝 Contributing

This is a private project for Ichiban Sushi, but improvements are welcome:

1. Test changes locally
2. Update documentation
3. Commit with clear messages
4. Deploy to staging first

## 📄 License

Private - © 2025 Ichiban Sushi / BlueHawana

## 🔗 Links

- **Frontend**: https://invoices.bluehawana.com
- **API**: https://invoices-api.bluehawana.com
- **Main Site**: https://www.bluehawana.com
- **Documentation**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)

## 📞 Support

For issues or questions:
1. Check logs: `./check_system.sh`
2. Run diagnostics: `python test_workflow.py`
3. Review documentation
4. Contact: hongyanab@gmail.com

---

**Built with ❤️ by [BlueHawana](https://www.bluehawana.com)**
