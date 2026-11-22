# 🧾 Invoice Processing System for Ichiban Sushi

Automated invoice collection, reconciliation, and printing system.

## 🚀 Quick Start - Print November Invoices

```bash
./setup_month.sh 2026 11
```

This ONE command:
- Updates system to November 2026
- Downloads all invoices (Foodora, Uber, Wolt, Stripe)
- Opens the website
- Waits for you to upload handwritten amounts
- Ready to print in 5 minutes

## 📋 What Happens Each Month

1. **You run:** `./setup_month.sh 2026 11`
2. **System downloads:** 30-38 invoices automatically
3. **You upload:** Photo of handwritten amounts
4. **System matches:** All invoices to handwritten amounts
5. **You print:** Click "Print All" or select specific invoices

**Total time: ~5 minutes**  
**Token cost: <$1 (previously $250!)**

## 📊 Monthly Invoice Breakdown

| Partner | Count | Source | Status |
|---------|-------|--------|--------|
| Foodora | 4-6 | Email | ✅ Auto |
| Uber | 4-5 | Email/Manual | ⚠️ Backup available |
| Wolt | 2 | Email | ✅ Auto |
| Stripe | 20-25 | API | ✅ Auto |

## 🌐 Access

- **Website:** https://invoices.bluehawana.com
- **Backend API:** https://api.bluehawana.com
- **No login required** - anyone can view and print

## 📖 Documentation

- **Complete Guide:** [MONTHLY_WORKFLOW.md](./MONTHLY_WORKFLOW.md)
- **Token Saving Guide:** [NEVER_WASTE_TOKENS_AGAIN.md](./NEVER_WASTE_TOKENS_AGAIN.md)

## 🛠️ Commands

```bash
# Setup November 2026
./setup_month.sh 2026 11

# Setup December 2026
./setup_month.sh 2026 12

# Create manual Uber invoices (if email sync fails)
python3 create_uber_manual.py 2026 11 2956.85 1214.85 1456.00 1771.50 1840.50

# Check status
curl -s "https://api.bluehawana.com/reconciliation-status" | python3 -m json.tool
```

## 🎯 System Features

- ✅ **Automatic invoice download** from 4 platforms
- ✅ **OCR handwriting recognition** for amounts
- ✅ **Payment period logic** (last 2 weeks prev month + current month)
- ✅ **PDF generation and printing** with browser compatibility
- ✅ **100% reconciliation** matching
- ✅ **Remote access** - print from anywhere
- ✅ **Token efficient** - <$1 per month vs $250

## 📁 Project Structure

```
.
├── frontend/              # Next.js web interface
│   ├── app/              # React components
│   └── out/              # Built static files
├── backend/              # FastAPI backend (on VPS)
│   ├── main.py          # Main reconciliation logic
│   ├── ocr_module.py    # PDF text extraction
│   ├── email_module.py  # Email invoice fetching
│   └── stripe_module.py # Stripe API integration
├── setup_month.sh        # 🎯 ONE-COMMAND MONTHLY SETUP
├── create_uber_manual.py # Backup for Uber invoices
└── MONTHLY_WORKFLOW.md   # Complete documentation
```

## 🔧 Technical Stack

- **Frontend:** Next.js 16, React 19, TailwindCSS 4, TypeScript
- **Backend:** FastAPI (Python), Uvicorn
- **OCR:** Tesseract via ocr_module
- **Deployment:** Cloudflare Pages (frontend), RackNerd VPS (backend)
- **Automation:** Bash scripts, GitHub Actions

## 📞 Support

If something breaks, check [MONTHLY_WORKFLOW.md](./MONTHLY_WORKFLOW.md) troubleshooting section.

Quick fixes:
- **Website shows old month:** Wait 5-10 min for auto-deploy
- **No invoices showing:** `ssh racknerd 'sudo systemctl restart invoice-backend'`
- **Uber invoices missing:** `python3 create_uber_manual.py 2026 11 [amounts]`

## 🎉 Success Metrics

- ✅ September 2026: 32/32 invoices (100%)
- ✅ October 2026: Setup automated
- ✅ Token usage: $250 → <$1 per month
- ✅ Setup time: Hours → 5 minutes
- ✅ Manual work: Eliminated 95%

---

**Last Updated:** November 22, 2026  
**Next Month:** Run `./setup_month.sh 2026 12` on December 1st
