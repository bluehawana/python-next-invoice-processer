#!/bin/bash
# Force production deployment to Cloudflare Pages

echo "🔨 Building..."
npm run build

echo ""
echo "🚀 Deploying to production..."
# Use production flag
CF_PAGES_BRANCH=main wrangler pages deploy out \
  --project-name=python-next-invoice-processer \
  --commit-dirty=true

echo ""
echo "✅ Check: https://invoices.bluehawana.com"
