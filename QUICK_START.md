# 🚀 QUICK START - MONTHLY INVOICES

No terminal, no commands, no redeploy. The site always works on the **previous calendar month**
(in November it shows October) and you can pick another month with the month picker.

## Every month (about 2 minutes)

1. **Take a photo** of the handwritten sheet
2. **Open** https://invoices.bluehawana.com
3. **Drag & drop** the photo onto "Handwritten Records"
4. Wait while it runs by itself:
   - AI reads the handwritten amounts
   - Stripe payouts + Wolt / Foodora / Uber invoices are collected
     (including the last two weeks of the previous month)
   - Every handwritten amount is matched to its invoice
5. **Click "Print all matched"** - one PDF opens, press Cmd+P once

Rows marked "no invoice found" are the only thing left to check by hand.

## After changing code

```bash
./setup_month.sh          # build + deploy frontend and backend
```

---

## If Uber Email Sync Fails

If you see "0 Uber invoices" after setup:

```bash
python3 create_uber_manual.py 2026 11 2956.85 1214.85 1456.00 1771.50 1840.50
```

(Replace the amounts with your actual November amounts)

---

## Troubleshooting

**Website still shows October:**
- Wait 5-10 minutes for Cloudflare to deploy
- Or refresh the page

**No invoices showing:**
```bash
ssh racknerd 'sudo systemctl restart invoice-backend'
```

**Need help:**
- Read: `MONTHLY_WORKFLOW.md` (complete guide)
- Read: `NEVER_WASTE_TOKENS_AGAIN.md` (troubleshooting)

---

## That's It!

**One command per month. Five minutes total. Done.**

No more $250 in tokens.  
No more hours of debugging.  
No more manual work.

Just run the script, upload photo, print. 🖨️
