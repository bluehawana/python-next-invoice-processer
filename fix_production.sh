#!/bin/bash

# Fix production deployment to ensure invoice collection works

echo "🔧 Fixing Production Invoice System..."
echo "========================================"

SERVER="racknerd"
REMOTE_DIR="/home/harvad/invoice-processor"

echo ""
echo "1. Checking backend service status..."
ssh $SERVER "sudo systemctl status invoice-backend --no-pager | head -20"

echo ""
echo "2. Checking if venv has all dependencies..."
ssh $SERVER << 'EOF'
cd /home/harvad/invoice-processor/backend
source venv/bin/activate
echo "Python version: $(python --version)"
echo "Checking key packages..."
python -c "import stripe; print('✅ stripe')" 2>/dev/null || echo "❌ stripe missing"
python -c "import boto3; print('✅ boto3')" 2>/dev/null || echo "❌ boto3 missing"
python -c "import playwright; print('✅ playwright')" 2>/dev/null || echo "❌ playwright missing"
python -c "import fpdf; print('✅ fpdf')" 2>/dev/null || echo "❌ fpdf missing"
EOF

echo ""
echo "3. Reinstalling dependencies if needed..."
ssh $SERVER << 'EOF'
cd /home/harvad/invoice-processor/backend
source venv/bin/activate
pip install -q -r requirements.txt
echo "✅ Dependencies updated"
EOF

echo ""
echo "4. Testing invoice collection..."
ssh $SERVER << 'EOF'
cd /home/harvad/invoice-processor/backend
source venv/bin/activate
python3 -c "
from stripe_module import download_stripe_payouts
from email_module import fetch_email_invoices
import os

print('Testing Stripe API...')
payouts = download_stripe_payouts(2025, 1)
print(f'✅ Found {len(payouts)} Stripe payouts')

print('Testing Email collection...')
emails = fetch_email_invoices(2025, 1)
print(f'✅ Found {len(emails)} email invoices')

print('Testing R2 storage...')
from r2_module import get_r2_client
s3 = get_r2_client()
if s3:
    print('✅ R2 connected')
else:
    print('❌ R2 connection failed')
"
EOF

echo ""
echo "5. Restarting backend service..."
ssh $SERVER "sudo systemctl restart invoice-backend"
sleep 3
ssh $SERVER "sudo systemctl status invoice-backend --no-pager | head -10"

echo ""
echo "6. Testing API endpoint..."
sleep 2
curl -s https://invoices-api.bluehawana.com/ | python3 -m json.tool || echo "❌ API not responding"

echo ""
echo "========================================"
echo "✅ Production fix complete!"
echo ""
echo "Next steps:"
echo "1. Test invoice collection: curl -X POST 'https://invoices-api.bluehawana.com/trigger-download?year=2025&month=1'"
echo "2. Check status: curl 'https://invoices-api.bluehawana.com/reconciliation-status'"
echo "3. View logs: ssh $SERVER 'sudo journalctl -u invoice-backend -f'"
