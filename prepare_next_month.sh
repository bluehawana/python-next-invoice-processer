#!/bin/bash

# Automated Monthly Update Script
# Usage: ./prepare_next_month.sh <year> <month>
# Example: ./prepare_next_month.sh 2026 9

if [ $# -ne 2 ]; then
    echo "Usage: $0 <year> <month>"
    echo "Example: $0 2026 9"
    exit 1
fi

YEAR=$1
MONTH=$2

echo "=========================================="
echo "Preparing for $YEAR-$(printf "%02d" $MONTH)"
echo "=========================================="

# Step 1: Update frontend display month
echo "1. Updating frontend display month..."
sed -i.bak "s/const DISPLAY_MONTH = { year: [0-9]*, month: [0-9]* }/const DISPLAY_MONTH = { year: $YEAR, month: $MONTH }/" frontend/app/page.tsx

# Step 2: Update backend month references
echo "2. Updating backend month references..."
# This requires manual review since there are multiple occurrences
echo "   Please manually update backend/main.py:"
echo "   - Line ~170: download_stripe_payouts($YEAR, $MONTH)"
echo "   - Line ~327: download_stripe_payouts($YEAR, $MONTH)"
echo "   - Line ~325: _filter_month_files(all_files, $YEAR, $MONTH)"

# Step 3: Commit changes
echo ""
echo "3. Review and commit changes:"
echo "   git diff"
echo "   git add frontend/app/page.tsx backend/main.py"
echo "   git commit -m 'Update to $YEAR-$(printf "%02d" $MONTH)'"
echo "   git push"

echo ""
echo "4. Deploy to VPS:"
echo "   ssh racknerd 'cd /home/harvad/invoice-processor/backend && git pull && sudo systemctl restart invoice-backend'"

echo ""
echo "5. Trigger sync:"
echo "   curl -X POST 'https://api.bluehawana.com/trigger-download?year=$YEAR&month=$MONTH'"

echo ""
echo "=========================================="
echo "✅ Preparation script complete"
echo "   Next: Upload handwritten data via API or web interface"
echo "=========================================="
