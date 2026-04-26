# VPS Deployment Guide

## 🚀 Deploy Updated Code to VPS

### Step 1: SSH into your VPS
```bash
ssh racknerd
```

### Step 2: Navigate to project directory
```bash
cd /path/to/python-next-invoice-processer
```

### Step 3: Pull latest changes
```bash
git pull origin main
```

### Step 4: Restart the backend service
```bash
# If using systemd
sudo systemctl restart backend

# OR if using PM2
pm2 restart backend

# OR if running manually
pkill -f "python main.py"
cd backend
source venv/bin/activate
nohup python main.py &
```

## ✅ What's New

1. **Uber invoices now show complete breakdown** (not just numbers)
2. **Easy CLI tool** to generate all invoices: `python generate_invoices.py 2026 3`
3. **New API endpoints** for monthly invoice generation
4. **Better documentation** for easy usage

## 🧪 Test on VPS

After deployment, test the new functionality:

```bash
cd backend
source venv/bin/activate

# Generate invoices for March 2026
python generate_invoices.py 2026 3 /tmp/test_invoices

# Check the output
ls -lh /tmp/test_invoices/
```

## 📋 Files Changed

- `backend/email_module.py` - Fixed Uber invoice format
- `backend/main.py` - Added new API endpoints
- `backend/generate_invoices.py` - New CLI tool
- `EASY_INVOICE_PRINTING.md` - User guide
- `INVOICE_GENERATION_GUIDE.md` - Technical guide

## 🔧 Configuration

Make sure your VPS `.env` file has:
```
STRIPE_API_KEY=sk_live_...
EMAIL_USER=hongyanab@gmail.com
EMAIL_PASS=your_app_password
INVOICE_STORAGE_PATH=backend/invoices
```

## 🆘 Troubleshooting

### If git pull fails
```bash
git stash
git pull origin main
git stash pop
```

### If service won't restart
```bash
# Check logs
sudo journalctl -u backend -n 50

# OR for PM2
pm2 logs backend
```

### Test the API
```bash
curl http://localhost:8000/
# Should return: {"status":"Invoice Processor API is running"}
```

## 📝 Next Steps

1. Pull the code on VPS
2. Restart the service
3. Test invoice generation
4. Use the new CLI tool for easy monthly invoice generation

## 💡 Usage on VPS

Generate invoices directly on VPS:
```bash
cd backend
source venv/bin/activate
python generate_invoices.py 2026 3 /var/www/invoices
```

Then access via:
```
https://api.bluehawana.com/static/invoices/ubereats_2.030.60.pdf
```
