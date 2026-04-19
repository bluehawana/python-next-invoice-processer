# Easy Invoice Printing - Quick Guide

## 🎯 What You Need to Do Each Month

Just run ONE command to generate all invoices:

```bash
cd backend
source venv/bin/activate
python generate_invoices.py 2026 3 ~/Desktop/final
```

Replace `2026 3` with your desired year and month.

## ✅ What This Does Automatically

1. **Fetches all Stripe payouts** for the month
2. **Generates Stripe PDF invoices** with full transaction details
3. **Downloads Uber Eats invoices** from email with proper Swedish format
4. **Downloads Wolt payout reports** (actual payment amounts)
5. **Downloads Foodora invoices** from email
6. **Saves everything** to your specified folder

## 📋 What You Get

### For March 2026, you'll get files like:

**Stripe** (20 files):
- `stripe_payout_po_1T6KwxGByRYD7y4l0nXPVMVe.pdf` (553.90 kr - Mar 2)
- `stripe_payout_po_1T6glOGByRYD7y4lP6AMJGje.pdf` (612.02 kr - Mar 3)
- ... and 18 more

**Uber Eats** (3 files with proper format):
- `ubereats_2.030.60.pdf` - Shows Totalbelopp, Uber avgift, Moms, etc.
- `ubereats_348.40.pdf`
- `ubereats_1.868.10.pdf`

**Wolt** (2 files):
- `wolt_XXXXX_payout_report_*.pdf`

**Foodora** (4 files):
- `foodora_XXXXX_Faktureringsdokument*.pdf`

## 🚀 Quick Commands

### Generate for current month
```bash
python generate_invoices.py 2026 4 ~/Desktop/invoices
```

### Generate for February
```bash
python generate_invoices.py 2026 2 ~/Desktop/feb
```

### Clean up old files
```bash
rm -f backend/invoices/*.pdf
```

## 🔧 What Was Fixed

1. ✅ Uber invoices now show **complete breakdown**:
   - Total försäljning (Totalbelopp)
   - Uber Eats-avgift
   - Moms på Uber Eats-avgift  
   - Nettoförsäljning
   - Total Betalning
   - Daily breakdown with dates

2. ✅ **One simple command** to generate everything

3. ✅ **Automatic filtering** - only gets relevant invoices for the month

4. ✅ **Clean output** - saves directly to your chosen folder

## 📝 Notes

- All old test PDFs have been deleted
- The system now uses the updated Uber format automatically
- Wolt: Only downloads payout reports (not fee invoices)
- Stripe: Generates full transaction details from API

## 🆘 If Something Goes Wrong

1. Check `.env` file has correct credentials
2. Make sure you're in the `backend` folder
3. Make sure virtual environment is activated (`source venv/bin/activate`)
4. Check the output for any error messages

## 💡 Pro Tips

- Run this at the beginning of each month for the previous month
- Save to a dated folder: `~/Desktop/invoices_2026_03`
- The script shows a summary of what was generated
- All files are ready to print immediately
