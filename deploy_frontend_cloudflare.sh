#!/bin/bash

echo "🚀 Deploying Frontend to Cloudflare Pages"
echo "=========================================="
echo ""

# Build the frontend
echo "📦 Building frontend..."
cd frontend
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Build successful!"
echo ""
echo "📤 Next steps:"
echo "1. Go to Cloudflare Pages dashboard"
echo "2. Select 'invoices.bluehawana.com' project"
echo "3. Click 'Create deployment'"
echo "4. Upload the 'frontend/out' folder"
echo ""
echo "Or use Wrangler CLI:"
echo "  npx wrangler pages deploy frontend/out --project-name=invoices-bluehawana"
echo ""
echo "✨ Frontend is ready for deployment!"
