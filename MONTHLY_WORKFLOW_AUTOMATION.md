# Monthly Invoice Reconciliation - AUTOMATED WORKFLOW

## 🎯 Goal
Never waste tokens debugging the same issues every month!

## ✅ Current Status (August 2026)
- ✅ **Stripe: 16/16** - Fully automated via API
- ✅ **Uber: 3/3** - Manual invoices work
- ✅ **Wolt: 2/2** - Email fetching works
- ❌ **Foodora: 3/5** - Need to improve automation

## 🔧 What Was Fixed This Month

### 1. Stripe Issues (SOLVED)
- Fixed payout month (was Sep, should be Aug)
- Fixed ID prefix calculation (Jan 2026 = 1N, Aug = 1U)  
- Fixed case-sensitivity bug (lowercase vs uppercase)
- Mapped payout IDs to PDF files (not dashboard URLs)
- Corrected amounts (removed duplicate, added 1065.12)

### 2. Business Logic (EMBEDDED IN CODE)
File: `backend/main.py` function `_filter_month_files()`

**Critical Rule:** Foodora & Uber have ~2 week payment delays
- Work done in last 2 weeks of PREVIOUS month gets paid in CURRENT month
- Example: August 2026 payment includes July 16-31 + August 1-15

## 📋 Next Month Workflow (September 2026)

### Step 1: Update Display Month
```bash
# File: frontend/app/page.tsx
# Change: const DISPLAY_MONTH = { year: 2026, month: 8 }
# To:     const DISPLAY_MONTH = { year: 2026, month: 9 }
```

### Step 2: Update Backend Endpoints
```bash
# File: backend/main.py
# Search for: 2026, 8
# Replace with: 2026, 9
# (3 occurrences in startup, upload-handwritten-manual, trigger-download)
```

### Step 3: Run Automated Sync
```bash
cd /Users/harvad/Projects/python-next-invoice-processer
git add frontend/app/page.tsx backend/main.py
git commit -m "Update to September 2026"
git push

ssh racknerd 'cd /home/harvad/invoice-processor/backend && git pull && sudo systemctl restart invoice-backend'

# Trigger invoice download
curl -X POST "https://api.bluehawana.com/trigger-download?year=2026&month=9"
```

### Step 4: Upload Handwritten Data
```bash
# Get your handwritten amounts from paper
# Then upload via API:
curl -X POST "https://api.bluehawana.com/upload-handwritten-manual" \
  -H "Content-Type: application/json" \
  -d '{
    "records": {
      "foodora": [amount1, amount2, ...],
      "uber": [amount1, amount2, ...],
      "wolt": [amount1, amount2],
      "stripe": [amount1, amount2, ...]
    }
  }'
```

### Step 5: Handle Missing Invoices
If any invoices are missing:

**For Foodora/Uber/Wolt:**
1. Download from partner dashboard
2. Rename to match pattern: `{partner}_{invoice_number}_Faktureringsdokument.pdf`
3. Upload:
```bash
scp invoice.pdf racknerd:/home/harvad/invoice-processor/backend/invoices/
ssh racknerd 'sudo systemctl restart invoice-backend'
```

**For Stripe:**
- Should be 100% automated (fetched from API)
- If missing, check Stripe API key in `.env`

## 🚀 Future Improvements

### Make it 100% Automatic
1. **OCR Feature** - Scan handwritten paper, extract amounts automatically
2. **Auto-month Detection** - Detect current month, no manual updates needed
3. **Email Notifications** - Alert when invoices ready for review
4. **Foodora API** - Replace manual uploads with API integration

### Better Foodora Handling
Current issue: Invoice numbers (7002xxxxxx) don't follow predictable pattern
- Need better filter or Foodora API integration
- Or: Store all Foodora invoices, filter by date range

## 📝 Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | Filter logic, endpoints, month configuration |
| `backend/stripe_module.py` | Stripe API integration |
| `backend/ocr_module.py` | Reconciliation matching logic |
| `frontend/app/page.tsx` | Display month configuration |
| `/home/harvad/invoice-processor/backend/handwritten_data_persistent.json` | Persisted handwritten amounts on VPS |

## 🆘 Troubleshooting

### Stripe PDFs showing 404
- Check: File paths use `/home/harvad/invoice-processor/backend/invoices/` not dashboard URLs
- Fix: Verify `ocr_module.py` maps payout IDs to PDF files

### Invoices not matching
- Check: Filter in `_filter_month_files()` includes correct month range
- Check: Invoice IDs are in expected range
- Fix: Adjust ID range or add manual override

### Handwritten data lost
- Check: `handwritten_data_persistent.json` exists on VPS
- Check: OCR feature not overwriting with empty data
- Fix: Always load from persistent file on startup

## 💾 Backup Strategy
```bash
# Backup handwritten data monthly
ssh racknerd 'cat /home/harvad/invoice-processor/backend/handwritten_data_persistent.json' > backup_$(date +%Y-%m).json

# Backup all invoices
ssh racknerd 'cd /home/harvad/invoice-processor/backend && tar -czf invoices_$(date +%Y-%m).tar.gz invoices/'
scp racknerd:/home/harvad/invoice-processor/backend/invoices_$(date +%Y-%m).tar.gz ~/backups/
```

## ✨ Success Metrics
- ✅ All 4 partners: 100% matched
- ✅ No missing invoices
- ✅ PDFs accessible and printable
- ✅ Total time: < 10 minutes per month

---
**Last Updated:** August 2026  
**Status:** Stripe fully automated, others need minor manual steps
