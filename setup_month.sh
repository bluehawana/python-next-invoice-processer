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

# One source of truth: the Mac repo -> GitHub -> VPS. Never edit code on the VPS.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "❌ You have uncommitted changes on the Mac. Commit them first so all sides get the same code."
    git status --short --untracked-files=no
    exit 1
fi

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
# Anything edited directly on the server is set aside (kept in git stash), then the server
# is made identical to GitHub main.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    git stash push -m "server-edits-$(date +%Y%m%d-%H%M%S)"
    echo "⚠️  Server had local edits - saved to git stash"
fi
git fetch origin main
git reset --hard origin/main
sudo systemctl restart invoice-backend
echo "Backend deployed and restarted"
ENDSSH
echo "   ✅ Backend deployed"

echo "🔍 [4/4] Verifying..."
LOCAL=$(git rev-parse --short HEAD)
VPS=$(ssh racknerd 'cd /home/harvad/invoice-processor && git rev-parse --short HEAD')
if [ "$LOCAL" = "$VPS" ]; then
    echo "   ✅ Mac, GitHub and VPS all on $LOCAL"
else
    echo "   ❌ Mac is on $LOCAL but VPS is on $VPS"
    exit 1
fi
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
