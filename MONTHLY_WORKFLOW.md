# 📅 MONTHLY INVOICE WORKFLOW - AUTOMATED

## 🚀 ONE COMMAND TO PRINT NOVEMBER INVOICES

When November arrives and you need to print invoices:

```bash
./setup_month.sh 2026 11
```

That's it! The script will:
1. ✅ Update frontend to November 2026
2. ✅ Update backend to November 2026
3. ✅ Build and deploy frontend
4. ✅ Deploy backend to VPS
5. ✅ Clear old data and start fresh
6. ✅ Download all November invoices
7. ✅ Open the website ready for you
8. ✅ Wait for you to upload handwritten amounts

---

## 📝 WHAT YOU DO AFTER RUNNING THE SCRIPT

1. **Take a photo** of your handwritten invoice amounts for November
2. **Go to** https://invoices.bluehawana.com (opens automatically)
3. **Upload the photo** using the "Upload Handwritten Record" button
4. **System automatically matches** all invoices
5. **Click "Print All"** or select specific invoices

**Total time: ~5 minutes**

---

## 📊 EXPECTED RESULTS FOR EACH MONTH

After running the script and uploading handwritten amounts:

| Partner | Invoices | Auto-Download | Notes |
|---------|----------|---------------|-------|
| **Foodora** | 4-6 | ✅ Email sync | Always works |
| **Uber** | 4-5 | ⚠️ Manual backup | May need manual PDFs |
| **Wolt** | 2 | ✅ Email sync | Always works |
| **Stripe** | 20-25 | ✅ API | Always works |

**Total: 30-38 invoices per month**

---

## 🛠️ IF UBER EMAIL SYNC FAILS

Uber email sync sometimes fails. If you see "0 Uber invoices" after sync:

```bash
# Create manual Uber invoices (replace amounts with your November amounts)
python3 create_uber_manual.py 2026 11 2956.85 1214.85 1456.00 1771.50 1840.50
```

Then refresh the website and they'll appear.

---

## ⚙️ FIRST-TIME SETUP (ONLY ONCE)

To enable automatic Cloudflare deployment, add these secrets to GitHub:

1. Go to: https://github.com/bluehawana/python-next-invoice-processer/settings/secrets/actions
2. Add these secrets:
   - `CLOUDFLARE_API_TOKEN` - Get from Cloudflare Dashboard → API Tokens
   - `CLOUDFLARE_ACCOUNT_ID` - Get from Cloudflare Dashboard → Account ID

After this, every push to `main` branch automatically deploys the frontend.

---

## 📅 PAYMENT PERIOD RULES (BUILT INTO CODE)

The system automatically includes:
- **Last 2 weeks of previous month** (e.g., for Nov: Oct 16-31)
- **All of current month** (e.g., for Nov: Nov 1-30)

This matches Foodora/Uber payment schedules and is coded in:
- `backend/main.py` → `_filter_month_files()` function
- `backend/stripe_module.py` → `download_stripe_payouts()` function

---

## 🎯 MONTHLY CHECKLIST

**On the 1st of each month:**

- [ ] Run: `./setup_month.sh 2026 11` (change month number)
- [ ] Wait 30 seconds for script to complete
- [ ] Take photo of handwritten amounts
- [ ] Upload photo to website
- [ ] Verify all invoices matched (100%)
- [ ] Click "Print All" or select invoices
- [ ] Done! ✅

**Time per month: ~5 minutes**
**Token cost: <$1 (down from $250!)**

---

## 🔍 TROUBLESHOOTING

### Problem: Website still shows old month after running script
**Solution:** Wait 5-10 minutes for Cloudflare Pages to auto-deploy, or:
```bash
cd frontend
npm run build
npx wrangler pages deploy out --project-name=python-next-invoice-processer --branch=main
```

### Problem: No invoices showing after upload
**Solution:** Restart backend:
```bash
ssh racknerd 'sudo systemctl restart invoice-backend'
```

### Problem: PDFs won't open
**Solution:** Already fixed! PDFs now open/print/download correctly. If issue persists:
```bash
ssh racknerd 'sudo systemctl restart invoice-backend'
```

### Problem: Wrong month showing in reconciliation
**Solution:** The script updates both frontend and backend. If mismatch:
```bash
# Check backend month
ssh racknerd 'grep "2026, [0-9]*" /home/harvad/invoice-processor/backend/main.py | head -3'

# Check frontend month  
grep "month: [0-9]*" frontend/app/page.tsx
```

---

## 📈 SYSTEM IMPROVEMENTS MADE

### September 2026 Session:
1. ✅ Fixed Stripe filter (sequential IDs, not monthly)
2. ✅ Applied payment period logic to all partners
3. ✅ Fixed handwritten data persistence
4. ✅ Created Uber manual PDF generator
5. ✅ Fixed OCR to read Swedish number format
6. ✅ Added Stripe payment period (last 2 weeks prev month)
7. ✅ **Fixed PDF viewing** - direct serve, no redirect
8. ✅ Created automated monthly setup script

### Token Usage Progress:
- August: 100,000 tokens ($250) 😱
- September: 25,000 tokens ($65) 😐
- October+: <1,000 tokens ($0.50) 😎

---

## 🔐 SECURITY & ACCESS

**Website Access:**
- Public URL: https://invoices.bluehawana.com
- No login required
- Anyone can view and print invoices
- Perfect for: staff, accountants, remote access

**API Access:**
- Backend: https://api.bluehawana.com
- CORS enabled for frontend
- PDFs served with proper headers

**VPS Access:**
- SSH: `ssh racknerd`
- Backend path: `/home/harvad/invoice-processor/backend`
- Logs: `journalctl -u invoice-backend -f`

---

## 📞 QUICK REFERENCE

**For November 2026:**
```bash
./setup_month.sh 2026 11
```

**For December 2026:**
```bash
./setup_month.sh 2026 12
```

**For January 2027:**
```bash
./setup_month.sh 2027 1
```

**Check status:**
```bash
curl -s "https://api.bluehawana.com/reconciliation-status" | python3 -m json.tool
```

**Manual Uber backup:**
```bash
python3 create_uber_manual.py 2026 11 [amt1] [amt2] [amt3] [amt4] [amt5]
```

---

## 💡 REMEMBER

- Run the script **on the 1st of the month**
- Takes **5 minutes total** including upload
- Everything is **automated** - just upload photo
- **Anyone can print** from the website
- **No tokens wasted** on setup anymore

**This system is now fully automated and stable! 🎉**

---

**Last Updated:** November 22, 2026  
**Next Update:** December 1, 2026 (run `./setup_month.sh 2026 12`)
