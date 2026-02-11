# 🚀 Deploying to Cloudflare Pages

## Overview

Your invoice system frontend is deployed on Cloudflare Pages at `invoices.bluehawana.com`.

## ✅ Already Configured

Based on your setup:
- ✅ Cloudflare Pages project created
- ✅ Domain `invoices.bluehawana.com` configured
- ✅ Environment variable `NEXT_PUBLIC_API_URL` set
- ✅ Connected to GitHub repository

## 📦 Build Configuration

### Cloudflare Pages Settings

```yaml
Framework preset: Next.js (Static HTML Export)
Build command: npm run build
Build output directory: out
Root directory: frontend
Node version: 18
```

### Environment Variables

Already set in Cloudflare Pages:
```
NEXT_PUBLIC_API_URL=https://invoices-api.bluehawana.com
```

## 🔄 Deployment Process

### Automatic Deployment

Every push to your main branch automatically triggers a deployment:

```bash
# Make changes
git add .
git commit -m "Update invoice system"
git push origin main

# Cloudflare Pages deploys automatically!
```

### Manual Deployment

If you need to manually trigger a deployment:

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to Pages → Your Project
3. Click "Create deployment"
4. Select branch and deploy

### Using Wrangler CLI

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy manually
cd frontend
npm run build
wrangler pages deploy out --project-name=invoice-system
```

## 🏗️ Build Process

The build creates a static export optimized for Cloudflare Pages:

```bash
cd frontend
npm install
npm run build
```

Output structure:
```
frontend/out/
├── index.html          # Main page
├── _next/
│   ├── static/        # Static assets
│   └── ...
└── ...
```

## 🌐 DNS Configuration

Your DNS is already configured in Cloudflare:

```
Type: CNAME
Name: invoices
Target: invoice-system.pages.dev (or your custom target)
Proxy: Enabled (orange cloud)
```

## 🔧 Troubleshooting

### Build Fails on Cloudflare

**Check build logs:**
1. Go to Cloudflare Dashboard → Pages
2. Select your project
3. Click on failed deployment
4. View build logs

**Common issues:**
```bash
# Node version mismatch
# Solution: Set Node version to 18 in Pages settings

# Missing dependencies
# Solution: Ensure package.json is in frontend/ directory

# Build command wrong
# Solution: Use "npm run build" not "next build"
```

### Site Not Updating

**Clear Cloudflare cache:**
1. Go to Cloudflare Dashboard → Caching
2. Click "Purge Everything"
3. Wait 30 seconds
4. Refresh your site

**Or use API:**
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID/purge_cache" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

### API Connection Issues

**Check CORS in backend:**

Edit `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://invoices.bluehawana.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Restart backend:**
```bash
ssh racknerd "sudo systemctl restart invoice-backend"
```

## 📊 Performance

Cloudflare Pages provides:
- **Global CDN**: 275+ data centers worldwide
- **Fast builds**: ~1-2 minutes
- **Instant rollbacks**: One-click rollback to previous versions
- **Preview deployments**: Every branch gets a preview URL
- **Analytics**: Built-in web analytics

## 🔐 Security

Cloudflare automatically provides:
- **SSL/TLS**: Free SSL certificate
- **DDoS protection**: Enterprise-grade protection
- **WAF**: Web Application Firewall
- **Bot protection**: Automatic bot mitigation

## 📈 Monitoring

### View Deployment Status

```bash
# Check current deployment
curl -I https://invoices.bluehawana.com

# View response headers
curl -v https://invoices.bluehawana.com 2>&1 | grep -i "cf-"
```

### Analytics

Access in Cloudflare Dashboard:
1. Go to Pages → Your Project
2. Click "Analytics" tab
3. View:
   - Page views
   - Unique visitors
   - Bandwidth usage
   - Geographic distribution

## 🚀 Deployment Workflow

### Development → Production

```bash
# 1. Develop locally
cd frontend
npm run dev

# 2. Test changes
# Open http://localhost:3000

# 3. Build locally to verify
npm run build

# 4. Commit and push
git add .
git commit -m "Feature: Add new functionality"
git push origin main

# 5. Cloudflare Pages deploys automatically
# Monitor at: https://dash.cloudflare.com/pages
```

### Preview Deployments

Create a branch for testing:
```bash
# Create feature branch
git checkout -b feature/new-design

# Make changes and push
git add .
git commit -m "Test new design"
git push origin feature/new-design

# Cloudflare creates preview URL:
# https://feature-new-design.invoice-system.pages.dev
```

## 🔄 Rollback

If something goes wrong:

1. Go to Cloudflare Dashboard → Pages → Your Project
2. Click "View build" on a previous successful deployment
3. Click "Rollback to this deployment"
4. Confirm rollback

Or keep the current deployment and fix forward:
```bash
git revert HEAD
git push origin main
```

## 📝 Build Logs

View detailed build logs:
1. Cloudflare Dashboard → Pages → Your Project
2. Click on any deployment
3. View "Build log" tab

Common log sections:
- **Initializing build environment**
- **Cloning repository**
- **Installing dependencies** (`npm install`)
- **Building application** (`npm run build`)
- **Deploying to Cloudflare's network**

## 🎯 Optimization Tips

### 1. Enable Cloudflare Speed Features

In Cloudflare Dashboard → Speed:
- ✅ Auto Minify (HTML, CSS, JS)
- ✅ Brotli compression
- ✅ Early Hints
- ✅ HTTP/3 (QUIC)

### 2. Configure Caching

Create `frontend/public/_headers`:
```
/*
  Cache-Control: public, max-age=3600, must-revalidate

/_next/static/*
  Cache-Control: public, max-age=31536000, immutable

/static/*
  Cache-Control: public, max-age=31536000, immutable
```

### 3. Add _redirects for SPA

Create `frontend/public/_redirects`:
```
/*    /index.html   200
```

## 🔗 Useful Links

- **Dashboard**: https://dash.cloudflare.com/pages
- **Docs**: https://developers.cloudflare.com/pages
- **Status**: https://www.cloudflarestatus.com
- **Community**: https://community.cloudflare.com

## 📞 Support

### Cloudflare Issues
- Dashboard: https://dash.cloudflare.com
- Support: https://support.cloudflare.com
- Community: https://community.cloudflare.com

### Application Issues
- Run diagnostics: `./check_system.sh`
- Check backend: `ssh racknerd "sudo systemctl status invoice-backend"`
- View logs: `ssh racknerd "sudo journalctl -u invoice-backend -f"`

## ✅ Deployment Checklist

- [x] Cloudflare Pages project created
- [x] GitHub repository connected
- [x] Build settings configured
- [x] Environment variables set
- [x] Domain configured
- [x] SSL certificate active
- [ ] Test deployment successful
- [ ] API connection verified
- [ ] All features working
- [ ] Mobile responsive checked

## 🎉 You're All Set!

Your invoice system is deployed on Cloudflare Pages with:
- ✅ Automatic deployments from GitHub
- ✅ Global CDN distribution
- ✅ Free SSL certificate
- ✅ DDoS protection
- ✅ Preview deployments for branches
- ✅ One-click rollbacks

**Live URL**: https://invoices.bluehawana.com

---

**Last Updated**: February 11, 2025  
**Platform**: Cloudflare Pages  
**Status**: ✅ Production Ready
