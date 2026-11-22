#!/bin/bash

# DEPLOY THE INVOICE SYSTEM (frontend -> Cloudflare Pages, backend -> VPS)
#
# Usage: ./setup_month.sh [year month]
#
# The website now works out the month by itself (always the previous calendar month,
# with a month picker to override), so NOTHING has to be edited or redeployed when a
# new month starts. Monthly routine = open https://invoices.bluehawana.com and drop
# the photo of the handwritten sheet.
#
# Run this script only after changing code. Passing a year and month additionally
# starts an invoice sync for that month.

set -e
cd "$(dirname "$0")"

# The Cloudflare Pages project that serves invoices.bluehawana.com
CF_PROJECT="python-next-invoice-processer"

echo "🔨 [1/4] Building frontend..."
(cd frontend && npm run build > /dev/null)
echo "   ✅ Frontend built"

echo "🚀 [2/4] Deploying frontend to Cloudflare Pages ($CF_PROJECT)..."
(cd frontend && npx wrangler pages deploy out --project-name="$CF_PROJECT" --branch=main --commit-dirty=true)
echo "   ✅ Frontend deployed"

echo "🚀 [3/4] Deploying backend to VPS..."
git push
ssh racknerd << 'ENDSSH'
set -e
cd /home/harvad/invoice-processor
git pull --ff-only
sudo systemctl restart invoice-backend
echo "Backend deployed and restarted"
ENDSSH
echo "   ✅ Backend deployed"

echo "🔍 [4/4] Verifying..."
sleep 5
curl -s "https://api.bluehawana.com/reconciliation-status" | python3 -c "
import json, sys
d = json.load(sys.stdin)
p = d.get('period', {})
print(f\"   ✅ Backend online, working on {p.get('year')}-{p.get('month'):02d}, {len(d['records'])} partners\")
"

if [ $# -eq 2 ]; then
    echo "📥 Starting invoice sync for $1-$2..."
    curl -s -X POST "https://api.bluehawana.com/trigger-download?year=$1&month=$2"
    echo ""
fi

echo ""
echo "🎯 Done: https://invoices.bluehawana.com"
