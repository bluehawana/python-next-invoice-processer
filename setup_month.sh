#!/bin/bash

# COMPLETE AUTOMATED MONTHLY INVOICE WORKFLOW
# Usage: ./setup_month.sh <year> <month>
# Example: ./setup_month.sh 2026 11
#
# This script does EVERYTHING:
# 1. Updates frontend to the new month
# 2. Updates backend to the new month  
# 3. Builds and deploys frontend to Cloudflare
# 4. Deploys backend to VPS
# 5. Clears old handwritten data
# 6. Triggers invoice sync
# 7. Waits for you to upload handwritten amounts
# 8. Opens the website ready for printing

set -e  # Exit on any error

if [ $# -ne 2 ]; then
    echo "Usage: $0 <year> <month>"
    echo "Example: $0 2026 11"
    exit 1
fi

YEAR=$1
MONTH=$2

# Month names for display
case $MONTH in
    1) MONTH_NAME="Jan";;
    2) MONTH_NAME="Feb";;
    3) MONTH_NAME="Mar";;
    4) MONTH_NAME="Apr";;
    5) MONTH_NAME="May";;
    6) MONTH_NAME="Jun";;
    7) MONTH_NAME="Jul";;
    8) MONTH_NAME="Aug";;
    9) MONTH_NAME="Sep";;
    10) MONTH_NAME="Oct";;
    11) MONTH_NAME="Nov";;
    12) MONTH_NAME="Dec";;
esac

echo ""
echo "════════════════════════════════════════════════════════"
echo "  AUTOMATED INVOICE SETUP FOR ${MONTH_NAME} ${YEAR}"
echo "════════════════════════════════════════════════════════"
echo ""

# Step 1: Update Frontend
echo "📝 [1/8] Updating frontend to ${MONTH_NAME} ${YEAR}..."
sed -i.bak "s/year: [0-9]*, month: [0-9]*/year: $YEAR, month: $MONTH/" frontend/app/page.tsx
sed -i.bak "s/display: '[A-Z][a-z]* [0-9]*'/display: '${MONTH_NAME} ${YEAR}'/" frontend/app/page.tsx
rm -f frontend/app/page.tsx.bak
echo "   ✅ Frontend updated"

# Step 2: Update Backend
echo "📝 [2/8] Updating backend to ${MONTH_NAME} ${YEAR}..."
ssh racknerd << ENDSSH
cd /home/harvad/invoice-processor/backend
python3 << 'ENDPYTHON'
import re
with open("main.py", "r") as f:
    content = f.read()

# Update all month references
content = re.sub(r'_filter_month_files\(([^,]+),\s*\d+,\s*\d+\)', r'_filter_month_files(\1, $YEAR, $MONTH)', content)
content = re.sub(r'download_stripe_payouts\(\d+,\s*\d+\)', 'download_stripe_payouts($YEAR, $MONTH)', content)

with open("main.py", "w") as f:
    f.write(content)
print("Backend updated")
ENDPYTHON
ENDSSH
echo "   ✅ Backend updated"

# Step 3: Build Frontend
echo "🔨 [3/8] Building frontend..."
cd frontend
npm run build > /dev/null 2>&1
cd ..
echo "   ✅ Frontend built"

# Step 4: Deploy Frontend to Cloudflare
echo "🚀 [4/8] Deploying frontend to Cloudflare Pages..."
cd frontend

# Create a deploy script that can run non-interactively
cat > deploy_to_cloudflare.sh << 'DEPLOYSCRIPT'
#!/bin/bash
export CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN}"
npx wrangler pages deploy out --project-name=invoices --commit-dirty=true
DEPLOYSCRIPT

chmod +x deploy_to_cloudflare.sh

# Try to deploy (will fail if no token, that's OK)
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "   ⚠️  CLOUDFLARE_API_TOKEN not set - skipping auto-deploy"
    echo "   📌 Cloudflare Pages will auto-deploy from GitHub in 5-10 minutes"
else
    ./deploy_to_cloudflare.sh
    echo "   ✅ Frontend deployed to Cloudflare"
fi
cd ..

# Step 5: Commit Changes
echo "💾 [5/8] Committing changes to git..."
git add frontend/app/page.tsx
git commit -m "Update to ${MONTH_NAME} ${YEAR} - automated by setup_month.sh" || echo "   ⚠️  No changes to commit"
git push
echo "   ✅ Changes pushed to GitHub"

# Step 6: Deploy Backend to VPS
echo "🚀 [6/8] Deploying backend to VPS..."
ssh racknerd << ENDSSH
cd /home/harvad/invoice-processor/backend
git pull
# Clear old handwritten data for new month
echo '{}' > handwritten_data_persistent.json
sudo systemctl restart invoice-backend
echo "Backend deployed and restarted"
ENDSSH
echo "   ✅ Backend deployed"

# Step 7: Trigger Invoice Sync
echo "📥 [7/8] Triggering invoice sync for ${MONTH_NAME} ${YEAR}..."
sleep 3
curl -s -X POST "https://api.bluehawana.com/trigger-download?year=${YEAR}&month=${MONTH}" > /dev/null
echo "   ✅ Invoice sync started"

# Step 8: Wait and check status
echo "⏳ [8/8] Waiting for invoices to download..."
sleep 10

# Check status
STATUS=$(curl -s "https://api.bluehawana.com/reconciliation-status")
TOTAL_FILES=$(echo "$STATUS" | python3 -c "import json,sys; data=json.load(sys.stdin); print(sum(len(r.get('files', [])) for r in data['records']))" 2>/dev/null || echo "0")

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ SETUP COMPLETE FOR ${MONTH_NAME} ${YEAR}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📊 Status:"
echo "   • Frontend: https://invoices.bluehawana.com"
echo "   • Backend: Running on VPS"
echo "   • Invoices downloaded: $TOTAL_FILES files"
echo ""
echo "📋 Next Steps:"
echo "   1. Take a photo of your handwritten invoice amounts"
echo "   2. Go to: https://invoices.bluehawana.com"
echo "   3. Upload the photo using 'Upload Handwritten Record'"
echo "   4. System will automatically match invoices"
echo "   5. Click 'Print All' or select specific invoices to print"
echo ""
echo "🎯 Ready to print ${MONTH_NAME} ${YEAR} invoices!"
echo ""

# Open the website
if command -v open &> /dev/null; then
    echo "🌐 Opening website..."
    open "https://invoices.bluehawana.com"
elif command -v xdg-open &> /dev/null; then
    xdg-open "https://invoices.bluehawana.com"
fi

echo "════════════════════════════════════════════════════════"
