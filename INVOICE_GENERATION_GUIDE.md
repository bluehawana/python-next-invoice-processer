# Invoice Generation Guide

## Quick Start - Generate Invoices for Any Month

### Method 1: Using the CLI Script (Easiest)

```bash
cd backend
source venv/bin/activate
python generate_invoices.py 2026 3 ~/Desktop/final
```

This will:
- Generate all Stripe payouts for March 2026
- Generate all Uber Eats invoices for March 2026
- Generate all Wolt invoices for March 2026
- Generate all Foodora invoices for March 2026
- Save everything to `~/Desktop/final`

### Method 2: Using the API

1. Start the server:
```bash
cd backend
source venv/bin/activate
python main.py
```

2. Generate invoices via API:
```bash
curl -X POST "http://localhost:8000/generate-monthly-invoices?year=2026&month=3"
```

3. Download as ZIP:
```bash
curl "http://localhost:8000/download-monthly-zip?year=2026&month=3" -o invoices_2026_03.zip
```

## What Gets Generated

### Stripe Invoices
- Format: `stripe_payout_po_XXXXX.pdf`
- Contains: Full payout details with transactions breakdown
- Shows: Charges, fees, refunds, adjustments

### Uber Eats Invoices
- Format: `ubereats_AMOUNT.pdf`
- Contains: Weekly payment summary with proper Swedish format
- Shows:
  - Total försäljning (Totalbelopp)
  - Uber Eats-avgift
  - Moms på Uber Eats-avgift
  - Nettoförsäljning
  - Total Betalning
  - Daily breakdown

### Wolt Invoices
- Format: `wolt_XXXXX_payout_report_*.pdf`
- Contains: Payout report (actual payment amount)
- Note: Only payout reports are downloaded, not fee invoices

### Foodora Invoices
- Format: `foodora_XXXXX_*.pdf`
- Contains: Invoice attachments from email

## Examples

### Generate for current month
```bash
python generate_invoices.py 2026 4 ~/Desktop/invoices
```

### Generate for February 2026
```bash
python generate_invoices.py 2026 2 ~/Desktop/feb_invoices
```

### Generate to default location (backend/invoices)
```bash
python generate_invoices.py 2026 3
```

## Cleaning Up

To delete all generated PDFs:
```bash
rm -f backend/invoices/*.pdf
```

Or via API:
```bash
curl -X POST "http://localhost:8000/delete-all-invoices"
```

## Troubleshooting

### No Uber invoices generated
- Check that emails exist for that month
- Uber sends weekly summaries, so there should be 4-5 per month
- Check email credentials in `.env`

### Stripe invoices missing
- Check Stripe API key in `.env`
- Verify payouts exist for that month in Stripe dashboard

### Wrong amounts
- Uber: Amounts are extracted from email body
- Stripe: Amounts come directly from Stripe API
- If amounts are wrong, check the source data

## Configuration

All settings are in `backend/.env`:
- `STRIPE_API_KEY`: Stripe API key
- `EMAIL_USER`: Gmail address
- `EMAIL_PASS`: Gmail app password
- `INVOICE_STORAGE_PATH`: Default output directory

## Notes

- Uber invoices now show complete breakdown (not just numbers)
- Wolt: Only payout reports are downloaded (actual payment amounts)
- Foodora: All invoice attachments are downloaded
- Stripe: Full transaction details with fees
