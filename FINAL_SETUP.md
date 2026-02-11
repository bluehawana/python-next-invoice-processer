# 🎯 Final Setup - API Subdomain

## Simple Solution

Use `api.bluehawana.com` for the backend API.

## 🚀 Quick Setup (5 minutes)

### Step 1: Add DNS Record in Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select `bluehawana.com` domain
3. Go to DNS → Records
4. Add A record:
   ```
   Type: A
   Name: api
   IPv4 address: 107.175.235.220
   Proxy status: DNS only (gray cloud)
   TTL: Auto
   ```
5. Save

### Step 2: Configure Nginx on VPS

```bash
# Upload nginx config
rsync deployment/nginx-api-subdomain.conf racknerd:/home/harvad/invoice-processor/deployment/

# Configure nginx
ssh racknerd "sudo cp /home/harvad/invoice-processor/deployment/nginx-api-subdomain.conf /etc/nginx/sites-available/api.bluehawana.com && sudo ln -sf /etc/nginx/sites-available/api.bluehawana.com /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx"

# Get SSL certificate
ssh racknerd "sudo certbot --nginx -d api.bluehawana.com --non-interactive --agree-tos -m admin@bluehawana.com"
```

### Step 3: Deploy Frontend

```bash
cd frontend
npm run build
cd ..
git add -A
git commit -m "Use api.bluehawana.com for backend"
git push origin main
```

## 🧪 Test

```bash
# Wait 2-3 minutes for DNS propagation
# Then test:
curl https://api.bluehawana.com/

# Should return:
# {"status":"Invoice Processor API is running"}
```

## ✅ Done!

Your system will use:
- **Frontend**: https://invoices.bluehawana.com (Cloudflare Pages)
- **Backend**: https://api.bluehawana.com (VPS)

No complex routing needed!
