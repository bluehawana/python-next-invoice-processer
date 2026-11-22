# 🚀 QUICK START - PRINT NOVEMBER INVOICES

## When November 1st Arrives

Open terminal and run:

```bash
cd /Users/harvad/Projects/python-next-invoice-processer
./setup_month.sh 2026 11
```

## What Happens Next (Automatic)

1. ✅ System updates to November 2026
2. ✅ Downloads all invoices from Foodora, Uber, Wolt, Stripe
3. ✅ Builds and deploys frontend
4. ✅ Deploys backend to VPS
5. ✅ Opens website in your browser
6. ⏳ Waits for you...

## What You Do (2 minutes)

1. **Take photo** of your handwritten November amounts with your phone
2. **Go to** https://invoices.bluehawana.com (already open)
3. **Click** "Upload Handwritten Record"
4. **Upload** the photo
5. **Wait** 10 seconds for OCR to process
6. **Click** "Print All" or select specific invoices

## Done! 🎉

All November invoices are now:
- ✅ Downloaded
- ✅ Matched to handwritten amounts
- ✅ Ready to print
- ✅ Accessible from anywhere (no VPN needed)

**Total time: 5 minutes**  
**Total cost: <$1 in tokens**

---

## For December

Same command, just change the month:

```bash
./setup_month.sh 2026 12
```

## For January 2027

```bash
./setup_month.sh 2027 1
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
