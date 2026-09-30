#!/bin/bash

# AUTOMATED MONTHLY SETUP - ONE COMMAND TO RULE THEM ALL
# Usage: ./monthly_setup.sh <year> <month>
# Example: ./monthly_setup.sh 2026 10

if [ $# -ne 2 ]; then
    echo "Usage: $0 <year> <month>"
    echo "Example: $0 2026 10"
    exit 1
fi

YEAR=$1
MONTH=$2

echo "=========================================="
echo "AUTOMATED MONTHLY SETUP: $YEAR-$(printf "%02d" $MONTH)"
echo "=========================================="

# Step 1: Update frontend
echo "[1/5] Updating frontend..."
sed -i.bak "s/year: [0-9]*, month: [0-9]*/year: $YEAR, month: $MONTH/" frontend/app/page.tsx

# Step 2: Update backend - all 3 locations at once
echo "[2/5] Updating backend..."
sed -i.bak "s/download_stripe_payouts([0-9]*, [0-9]*)/download_stripe_payouts($YEAR, $MONTH)/g" backend/main.py
sed -i.bak "s/_filter_month_files([^,]*, [0-9]*, [0-9]*)/_filter_month_files(\\1, $YEAR, $MONTH)/g" backend/main.py

# Step 3: Commit and push
echo "[3/5] Committing changes..."
git add frontend/app/page.tsx backend/main.py
git commit -m "Update to $YEAR-$(printf "%02d" $MONTH)"
git push

# Step 4: Deploy to VPS
echo "[4/5] Deploying to VPS..."
ssh racknerd << ENDSSH
cd /home/harvad/invoice-processor/backend
git pull
echo '{}' > handwritten_data_persistent.json
sudo systemctl restart invoice-backend
ENDSSH

# Step 5: Trigger sync
echo "[5/5] Triggering invoice sync..."
sleep 3
curl -X POST "https://api.bluehawana.com/trigger-download?year=$YEAR&month=$MONTH"

echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Take a photo of your handwritten paper"
echo "2. Send photo to: https://invoices.bluehawana.com"
echo "3. System will OCR and upload automatically"
echo ""
echo "OR manually upload via API:"
echo "curl -X POST 'https://api.bluehawana.com/upload-handwritten-manual' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"records\":{\"foodora\":[...],\"uber\":[...],\"wolt\":[...],\"stripe\":[...]}}'"
echo ""
echo "Check status: https://invoices.bluehawana.com"
echo "=========================================="
