# How to Prevent Missing Invoices

## 🎯 The Problem We Solved

**July 2026 Issue:** Uber Eats week 3 invoice (2,253 kr) was missing because:
- Uber didn't send an email notification
- Only found it manually in the Uber Eats dashboard

## ✅ New Solution: Smart Invoice Sync Workflow

### Complete Workflow (5 Steps)

```
1. Handwritten Paper → OCR
2. Email Sync
3. Completeness Check
4. Portal Fetch (if missing)
5. Reconciliation
```

---

## 📋 Step-by-Step Usage

### Option 1: Automated Workflow (Recommended)

```bash
cd backend
source venv/bin/activate

# Run the smart sync for a month
python smart_invoice_sync.py 2026 8 ~/Downloads/handwritten_income.heic
```

This will:
1. ✅ Extract amounts from your handwritten paper (OCR)
2. ✅ Fetch all invoices from emails
3. ✅ Check if any are missing
4. ⚠️ Alert you to download from partner portals if needed
5. ✅ Reconcile everything

### Option 2: Manual Checking

```bash
cd backend
source venv/bin/activate

# Check a specific month for missing invoices
python invoice_checker.py 2026 8

# Check last month
python invoice_checker.py last

# Check current month
python invoice_checker.py current
```

---

## 🔍 What Gets Checked

### Expected Invoice Counts per Month:

| Partner | Expected | Notes |
|---------|----------|-------|
| **Uber Eats** | 3-5 emails | Weekly reports (sometimes 3, sometimes 5) |
| **Foodora** | 2 emails | Semi-monthly (1st-15th, 16th-31st) |
| **Wolt** | 2 emails | Semi-monthly payout reports |
| **Stripe** | Variable | Based on daily payouts |

---

## 🚨 If Invoices Are Missing from Email

### Uber Eats
1. Go to: https://restaurant.uber.com/payments
2. Login with: `hongyanab@gmail.com`
3. Filter by date range (the month you need)
4. Download each weekly payment report
5. Save PDFs to `backend/invoices/` with prefix `ubereats_`

**Transaction ID:** Look for "Transaktions-ID" in each report

### Foodora
1. Go to: https://partner.foodora.se
2. Navigate to "Fakturor" or "Invoices"
3. Download semi-monthly invoices
4. Save to `backend/invoices/` with prefix `foodora_`

### Wolt
1. Go to: https://restaurant.wolt.com/payments
2. Download payout reports
3. Save to `backend/invoices/` with prefix `wolt_`

---

## 📝 Manual Invoice Creation (Last Resort)

If a partner invoice is completely missing (no email, no portal access):

```bash
cd backend
source venv/bin/activate

# Create manual invoice (example for Uber Eats)
python create_manual_invoice.py uber 2026 8 2253.00 "2026-07-13" "2026-07-19"
```

---

## 🔄 Monthly Checklist

### Beginning of Month (Day 1-5):
- [ ] Take photo of handwritten income records
- [ ] Run smart sync: `python smart_invoice_sync.py <year> <month> <image>`
- [ ] Check for missing invoices
- [ ] Download any missing from partner portals

### Mid-Month (Day 15-20):
- [ ] Verify semi-monthly invoices arrived (Foodora, Wolt)
- [ ] Run checker: `python invoice_checker.py current`

### End of Month (Day 28-31):
- [ ] Final check: `python invoice_checker.py current`
- [ ] Generate all invoices: `python generate_invoices.py <year> <month>`
- [ ] Reconcile with bank statements

---

## 🛠️ Troubleshooting

### "Uber Eats: NO EMAILS found"
→ Some weeks Uber doesn't send emails. Check dashboard manually.

### "Foodora: Only 1 email found (expected 2)"
→ One semi-monthly invoice is missing. Check partner portal.

### "OCR failed"
→ Image quality issue. Try:
- Better lighting
- Flatten paper (remove creases)
- Convert HEIC to JPG first

### "Reconciliation mismatch"
→ Amounts don't match between handwritten and invoices
- Check for typos in handwritten records
- Verify invoice dates (might be from different month)
- Check if invoice includes fees/adjustments

---

## 📊 Reports Location

All check reports are saved to:
```
backend/invoice_reports/invoice_check_YYYY_MM.txt
```

---

## 🎓 Why This Works

1. **OCR** extracts your handwritten amounts (ground truth)
2. **Email sync** gets most invoices automatically
3. **Checker** identifies gaps by comparing email count vs expectations
4. **Portal fetch** fills gaps when emails are missing
5. **Reconciliation** matches everything together

**Result:** Zero missing invoices! 🎉

---

## 🚀 Future Improvements

### Phase 1: ✅ Done
- OCR handwriting recognition
- Email invoice fetching
- Invoice completeness checker
- Manual invoice creation

### Phase 2: 🔄 In Progress
- Partner portal web scraping (Selenium)
- Automated portal login

### Phase 3: 📅 Planned
- API integrations (Uber Eats API, Wolt API)
- Automated monthly reminders
- Dashboard alerts for missing invoices
- Automatic retry logic

---

## 📞 Quick Commands Reference

```bash
# Check if August 2026 is complete
python invoice_checker.py 2026 8

# Run full sync with OCR
python smart_invoice_sync.py 2026 8 ~/Downloads/income.heic

# Generate all invoices after fixing issues
python generate_invoices.py 2026 8

# Create manual invoice
python create_uber_2253_invoice.py
```

---

**Remember:** The key is to check early and often. Run the checker at the beginning, middle, and end of each month to catch missing invoices before they become a problem!
