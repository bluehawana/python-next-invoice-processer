# Deploying Invoice System to Vercel

## 🚀 Quick Deploy to Vercel

### Prerequisites
- GitHub account
- Vercel account (free tier works)
- Domain: invoices.bluehawana.com

### Step 1: Push to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Invoice system with BlueHawana styling"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/invoice-processor.git
git push -u origin main
```

### Step 2: Import to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `out`

### Step 3: Environment Variables

Add these environment variables in Vercel:

```
NEXT_PUBLIC_API_URL=https://invoices-api.bluehawana.com
```

### Step 4: Custom Domain

1. In Vercel project settings, go to "Domains"
2. Add domain: `invoices.bluehawana.com`
3. Follow DNS configuration instructions:

**For Cloudflare DNS:**
```
Type: CNAME
Name: invoices
Target: cname.vercel-dns.com
Proxy: DNS only (gray cloud)
```

**Or use A record:**
```
Type: A
Name: invoices
Target: 76.76.21.21
Proxy: DNS only
```

### Step 5: Deploy

Vercel will automatically deploy on every push to main branch.

**Manual deploy:**
```bash
cd frontend
npm install -g vercel
vercel --prod
```

## 🎨 Design Features

The new design matches www.bluehawana.com with:

- **Dark theme**: Slate-950 background with gradient
- **Blue/Cyan accents**: Matching your brand colors
- **Modern cards**: Glass-morphism effect with backdrop blur
- **Smooth animations**: Hover effects and transitions
- **Responsive**: Mobile-first design
- **Professional**: Clean, technical aesthetic

## 🔧 Local Development

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

## 📦 Build for Production

```bash
cd frontend
npm run build
```

This creates a static export in `frontend/out/` that Vercel will serve.

## 🌐 Architecture

```
┌─────────────────────────────────────┐
│  invoices.bluehawana.com (Vercel)   │
│  - Next.js Static Export            │
│  - React Frontend                   │
└──────────────┬──────────────────────┘
               │ API Calls
               ▼
┌─────────────────────────────────────┐
│ invoices-api.bluehawana.com (VPS)   │
│  - FastAPI Backend                  │
│  - Python Invoice Processing        │
│  - R2 Storage Integration           │
└─────────────────────────────────────┘
```

## 🎯 Features Implemented

### Visual Improvements
- ✅ Dark gradient background matching main site
- ✅ Blue/cyan color scheme
- ✅ Modern card designs with borders
- ✅ Animated status indicators
- ✅ Icon-enhanced sections
- ✅ Improved typography
- ✅ Better spacing and layout
- ✅ Responsive grid system
- ✅ Custom scrollbar styling
- ✅ Smooth transitions

### Functional Features
- ✅ Real-time invoice syncing
- ✅ Partner status monitoring
- ✅ File upload with drag & drop
- ✅ Batch printing
- ✅ Reconciliation table
- ✅ PDF viewing
- ✅ Progress indicators

## 🔄 Continuous Deployment

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update invoice system"
git push

# Vercel deploys automatically!
```

## 📊 Performance

The static export ensures:
- **Fast loading**: No server-side rendering overhead
- **Global CDN**: Vercel's edge network
- **Caching**: Automatic asset optimization
- **SEO**: Pre-rendered HTML

## 🐛 Troubleshooting

### API Connection Issues

If frontend can't connect to API:

1. Check CORS settings in `backend/main.py`:
```python
allow_origins=[
    "https://invoices.bluehawana.com",
    "http://localhost:3000",
]
```

2. Verify API is running:
```bash
curl https://invoices-api.bluehawana.com/
```

### Build Failures

Clear cache and rebuild:
```bash
cd frontend
rm -rf .next out node_modules
npm install
npm run build
```

### Domain Not Working

1. Check DNS propagation: https://dnschecker.org
2. Verify Vercel domain settings
3. Ensure SSL certificate is active

## 📱 Mobile Optimization

The design is fully responsive:
- **Mobile**: Single column layout
- **Tablet**: 2-column grid
- **Desktop**: Full 2-column with expanded table

## 🎨 Customization

To adjust colors, edit `frontend/app/globals.css`:

```css
:root {
  --background: #020617;      /* Main background */
  --foreground: #f8fafc;      /* Text color */
  --accent-blue: #3b82f6;     /* Primary accent */
  --accent-cyan: #06b6d4;     /* Secondary accent */
}
```

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Vercel project created
- [ ] Environment variables set
- [ ] Custom domain configured
- [ ] DNS records updated
- [ ] SSL certificate active
- [ ] API CORS configured
- [ ] Test invoice sync
- [ ] Test file upload
- [ ] Test printing
- [ ] Mobile responsive check

## 🎉 Success!

Your invoice system is now live with professional BlueHawana styling!

**URLs:**
- Frontend: https://invoices.bluehawana.com
- API: https://invoices-api.bluehawana.com
- Main Site: https://www.bluehawana.com
