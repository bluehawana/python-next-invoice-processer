# 🌐 Single Domain Setup Guide

## Overview

Configure both frontend and backend to use the same domain: **invoices.bluehawana.com**

### Architecture

```
invoices.bluehawana.com
├── /              → Cloudflare Pages (Frontend)
├── /api/*         → VPS Nginx → FastAPI Backend (port 8000)
└── /static/*      → VPS Nginx → Invoice files
```

## ✅ What's Been Updated

### Frontend
- ✅ API URL changed to: `https://invoices.bluehawana.com/api`
- ✅ Next.js config updated
- ✅ Environment variables configured

### Backend
- ✅ CORS updated to allow `invoices.bluehawana.com`
- ✅ Nginx config created for `/api` path
- ✅ Deployment script ready

## 🚀 Deployment Steps

### Step 1: Deploy Backend (5 minutes)

```bash
# Run the setup script
./deployment/setup_single_domain.sh
```

This will:
1. Sync backend code to VPS
2. Install dependencies
3. Configure nginx for `/api` path
4. Setup systemd service
5. Configure SSL certificate

### Step 2: Update Cloudflare Pages (2 minutes)

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to Pages → Your Project → Settings → Environment Variables
3. Update or add:
   ```
   NEXT_PUBLIC_API_URL=https://invoices.bluehawana.com/api
   ```
4. Save changes

### Step 3: Deploy Frontend (3 minutes)

```bash
# Build with new API URL
cd frontend
npm run build

# Commit and push
cd ..
git add .
git commit -m "Configure single domain for frontend and backend"
git push origin main

# Cloudflare Pages deploys automatically!
```

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl https://invoices.bluehawana.com/api/

# Should return:
# {"status":"Invoice Processor API is running"}

# Test reconciliation endpoint
curl https://invoices.bluehawana.com/api/reconciliation-status

# Should return JSON with partner status
```

### Test Frontend

1. Visit: https://invoices.bluehawana.com
2. Open browser console (F12)
3. Click "Sync Invoices"
4. Check Network tab - should see requests to `/api/*`
5. No CORS errors should appear

## 📋 URL Mapping

| Path | Served By | Purpose |
|------|-----------|---------|
| `/` | Cloudflare Pages | Frontend UI |
| `/api/*` | VPS Nginx → FastAPI | Backend API |
| `/static/invoices/*` | VPS Nginx | Invoice PDFs |
| `/health` | VPS Nginx → FastAPI | Health check |

## 🔧 Configuration Files

### Frontend
- `frontend/app/page.tsx` - API URL updated
- `frontend/next.config.ts` - Default API URL
- `frontend/.env.local` - Local development

### Backend
- `backend/main.py` - CORS updated
- `deployment/nginx-single-domain.conf` - Nginx config
- `deployment/backend.service` - Systemd service

## 🐛 Troubleshooting

### Backend Not Accessible

**Check nginx:**
```bash
ssh racknerd "sudo nginx -t"
ssh racknerd "sudo systemctl status nginx"
```

**Check backend service:**
```bash
ssh racknerd "sudo systemctl status invoice-backend"
ssh racknerd "sudo journalctl -u invoice-backend -n 50"
```

**Test locally on VPS:**
```bash
ssh racknerd "curl http://localhost:8000/"
```

### CORS Errors

**Check backend CORS settings:**
```bash
ssh racknerd "grep -A 10 'CORSMiddleware' /home/harvad/invoice-processor/backend/main.py"
```

Should include: `"https://invoices.bluehawana.com"`

**Restart backend:**
```bash
ssh racknerd "sudo systemctl restart invoice-backend"
```

### Frontend Can't Connect

**Check environment variable in Cloudflare:**
- Dashboard → Pages → Settings → Environment Variables
- Should be: `NEXT_PUBLIC_API_URL=https://invoices.bluehawana.com/api`

**Check browser console:**
- F12 → Console tab
- Look for API URL in network requests
- Should be: `https://invoices.bluehawana.com/api/*`

**Rebuild frontend:**
```bash
cd frontend
rm -rf .next out
npm run build
git add . && git commit -m "Rebuild" && git push
```

## 📊 Verification Checklist

- [ ] Backend accessible at `/api/`
- [ ] Returns: `{"status":"Invoice Processor API is running"}`
- [ ] SSL certificate active (https)
- [ ] Frontend loads at root `/`
- [ ] No CORS errors in console
- [ ] Invoice sync works
- [ ] File upload works
- [ ] Printing works

## 🔄 Local Development

For local development, use localhost:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py
# Runs on http://localhost:8000

# Terminal 2: Frontend
cd frontend
npm run dev
# Runs on http://localhost:3000
# Uses NEXT_PUBLIC_API_URL=http://localhost:8000 from .env.local
```

## 🎯 Benefits of Single Domain

✅ **Simpler DNS**: Only one domain to manage
✅ **No CORS issues**: Same origin for frontend and backend
✅ **Easier SSL**: One certificate for both
✅ **Better security**: No cross-domain requests
✅ **Cleaner URLs**: `/api/*` instead of separate subdomain

## 📞 Support

If you encounter issues:

1. **Check logs:**
   ```bash
   ssh racknerd "sudo journalctl -u invoice-backend -f"
   ```

2. **Test backend directly:**
   ```bash
   curl https://invoices.bluehawana.com/api/
   ```

3. **Check nginx:**
   ```bash
   ssh racknerd "sudo nginx -t && sudo systemctl status nginx"
   ```

4. **Restart services:**
   ```bash
   ssh racknerd "sudo systemctl restart invoice-backend nginx"
   ```

## 🎉 Success!

Once deployed, your system will have:
- ✅ Single domain for everything
- ✅ Frontend on Cloudflare Pages
- ✅ Backend API at `/api/*`
- ✅ No CORS issues
- ✅ SSL everywhere

---

**Domain**: invoices.bluehawana.com  
**Frontend**: Cloudflare Pages  
**Backend**: VPS (port 8000) via Nginx  
**Status**: Ready to deploy
