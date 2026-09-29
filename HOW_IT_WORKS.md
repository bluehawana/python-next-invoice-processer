# Invoice Reconciliation System - How It Works

## Summary
The system matches handwritten income records against digital invoices for monthly accounting.

## Key Concept: Payment Timing
**Important**: Payments received in August include work from the last 2 weeks of July due to payment terms.

### Payment Periods by Partner
- **Foodora**: August payment = last 2 weeks of July + first 2 weeks of August
- **Uber Eats**: August payment = last 2 weeks of July + first 2 weeks of August  
- **Wolt**: Semi-monthly periods clearly labeled in filename (e.g., `2026-07-16__2026-08-01`)
- **Stripe**: Daily payouts, filtered by payout date

## Monthly Workflow (Smooth as Butter)

### 1. Write Down Income (Paper)
Write down ALL income amounts received during the month from:
- Foodora (typically 4-5 invoices)
- Uber Eats (typically 3 invoices)
- Wolt (typically 2 invoices)
- Stripe (typically 16 payments)

### 2. Go to Website
Visit: https://invoices.bluehawana.com

### 3. Upload Photo (Option A - Automatic)
- Take photo of handwritten paper
- Click "Upload" in "Handwritten Records" section
- System uses OCR to extract amounts
- **Note**: OCR may fail - if it does, use Option B

### 4. Manual Entry (Option B - Reliable)
If OCR fails, manually enter via API:
```bash
curl -X POST "https://api.bluehawana.com/upload-handwritten-manual" \
  -H "Content-Type: application/json" \
  -d '{
    "records": {
      "Foodora": [amount1, amount2, amount3, amount4, amount5],
      "Uber": [amount1, amount2, amount3],
      "Wolt": [amount1, amount2],
      "Stripe": [amount1, amount2, ..., amount16]
    }
  }'
```

### 5. Click "Sync Invoices"
- Fetches invoices from Stripe API
- Fetches invoices from Gmail (Foodora, Uber, Wolt)
- Matches handwritten amounts to PDFs
- Shows results with green checkmarks ✓

### 6. Review & Print
- Check all partners show "✓ Matched"
- Click "Print" buttons to print matched invoices
- Done!

## Data Persistence

### What Persists Across Restarts
✅ **Handwritten data** - Saved to `handwritten_data_persistent.json`  
✅ **PDF invoices** - Stored in `backend/invoices/` directory  
✅ **Configuration** - API keys, email settings in `.env`

### What Doesn't Persist
❌ Reconciliation state (regenerated from handwritten + PDFs on startup)

## File Naming Conventions

### Foodora
Format: `foodora_[ID]_Faktureringsdokument - [InvoiceNumber].pdf`
- Example: `foodora_11907_Faktureringsdokument - 7002778490.pdf`
- Invoice number visible in email subject: "Ert underlag från Foodora: 7002778490"

### Uber Eats
Format: `ubereats_[ID]_email_body.pdf` (from email)
- Or: `ubereats_aug2026_week[N]_[amount]_manual.pdf` (manually created)

### Wolt
Format: `wolt_[ID]_Ichiban Sushi__payout_report__semi_monthly__[start]__[end].pdf`
- Example: `wolt_11913_Ichiban Sushi__payout_report__semi_monthly__2026-08-01__2026-08-16.pdf`
- Date range in filename tells you the period

### Stripe
Format: `stripe_payout_po_[PayoutID].pdf`
- Example: `stripe_payout_po_1U09ZJGByRYD7y4lXBZdsWTv.pdf`

## August 2026 Filter Logic

The system filters files for "August payment period":

```python
def _filter_aug2026_files(files):
    """August payments include last 2 weeks of July"""
    - Foodora: IDs 11850-11950 (covers late July + August)
    - Uber: IDs 11700-11900 (covers late July + August)
    - Wolt: Filenames containing "2026-08" or "2026-07-16__2026-08-01"
    - Stripe: Payout IDs starting with "po_1U" (August 2026 range)
```

## Troubleshooting

### "No invoice found" for amounts you wrote
**Cause**: The invoice for that amount doesn't exist in emails  
**Fix**: 
1. Check email for that invoice
2. Forward it to the Gmail account the system checks
3. Click "Sync Invoices" again

### OCR fails when uploading photo
**Cause**: Ollama not running, or API keys missing  
**Fix**: Use manual entry (Option B above)

### Handwritten data disappears after restart
**Fixed**: Now persists to `handwritten_data_persistent.json`

### "Sync Invoices" breaks reconciliation
**Fixed**: Now filters to current month only and preserves handwritten data

## Tech Stack
- **Frontend**: Next.js on Cloudflare Pages (invoices.bluehawana.com)
- **Backend**: FastAPI on RackNerd VPS (api.bluehawana.com)
- **Database**: JSON files + PDF storage
- **OCR**: Z.AI API / OpenAI GPT-4 Vision

## Quick Commands

### Check Status
```bash
curl -s "https://api.bluehawana.com/reconciliation-status" | jq
```

### Trigger Sync
```bash
curl -X POST "https://api.bluehawana.com/trigger-download?year=2026&month=8"
```

### Restart Backend
```bash
ssh racknerd "sudo systemctl restart invoice-backend"
```

### View Logs
```bash
ssh racknerd "journalctl -u invoice-backend -f"
```

## Next Month Preparation

For **September 2026**:
1. Update filter in `_filter_aug2026_files()` to `_filter_sep2026_files()`
2. Change ID ranges:
   - Foodora: 11950-12050
   - Uber: 11900-12100
   - Wolt: Look for "2026-09" in filename
   - Stripe: Payout IDs starting with "po_1V" or later
3. Update frontend `page.tsx` to show "Sep 2026"
4. Repeat smooth workflow above

---

**Last Updated**: September 29, 2026  
**System Status**: ✅ Working smoothly
