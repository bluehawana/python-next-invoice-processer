#!/bin/bash

echo "🚀 Deploying Invoice System Frontend to Cloudflare Pages"
echo "========================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    echo "   Run this script from the project root"
    exit 1
fi

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the project
echo ""
echo "🔨 Building Next.js project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ Build successful!"
echo ""

# Check if wrangler CLI is installed
if ! command -v wrangler &> /dev/null; then
    echo "📥 Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

echo ""
echo "🔐 Logging in to Cloudflare..."
wrangler login

echo ""
echo "🌐 Deploying to Cloudflare Pages..."
echo ""

# Deploy to Cloudflare Pages
# Note: Replace 'invoice-system' with your actual project name if different
wrangler pages deploy out --project-name=invoice-system

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================="
    echo "✅ Deployment complete!"
    echo ""
    echo "Your invoice system should now be live at:"
    echo "https://invoices.bluehawana.com"
    echo ""
    echo "Preview URL (if available):"
    echo "Check Cloudflare Dashboard for preview link"
    echo ""
    echo "Next steps:"
    echo "1. Visit https://invoices.bluehawana.com"
    echo "2. Test invoice sync functionality"
    echo "3. Verify API connection"
    echo "4. Check mobile responsiveness"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if you're logged in: wrangler whoami"
    echo "2. Verify project name in Cloudflare Dashboard"
    echo "3. Check build output exists: ls -la out/"
    echo ""
    exit 1
fi
