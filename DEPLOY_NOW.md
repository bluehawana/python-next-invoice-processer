# 🚀 Deploy Single Domain Configuration

## Quick Deploy Guide

Your system is now configured to use a single domain: **invoices.bluehawana.com**

## ✅ What's Ready

- ✅ Frontend code updated (API URL: `/api`)
- ✅ Backend CORS updated
- ✅ Nginx configuration created
- ✅ Deployment script ready
- ✅ Code pushed to GitHub

## 🎯 Deploy in 2 Steps

### Step 1: Deploy Backend (5 min)

```bash
./deployment/setup_single_domain.sh
```

This configures your VPS to serve the backend API at `/api/*`

### Step 2: Update Cloudflare Pages (2 min)

1. Go to: https://dash.cloudflare.com
2. Pages → Your Project → Settings → Environment Variables
3. Add/Update:
   ```
   NEXT_PUBLIC_API_URL=https://invoices.bluehawana.com/api
   ```
4. Save

Cloudflare will automatically rebuild and deploy!

## 🧪 Test After Deployment

```bash
# Test backend API
curl https://invoices.bluehawana.com/api/

# Should return:
# {"status":"Invoice Processor API is running"}
```

Then visit: https://invoices.bluehawana.com

## 📋 Architecture

```
invoices.bluehawana.com
├── /              → Cloudflare Pages (Frontend)
├── /api/*         → VPS Backend (FastAPI)
└── /static/*      → VPS (Invoice files)
```

## 🎉 Benefits

- ✅ Single domain (no -api subdomain needed)
- ✅ No CORS issues
- ✅ Simpler DNS
- ✅ One SSL certificate

## 📞 Need Help?

See: [SINGLE_DOMAIN_SETUP.md](SINGLE_DOMAIN_SETUP.md) for detailed guide

---

**Ready to deploy?** Run: `./deployment/setup_single_domain.sh`
