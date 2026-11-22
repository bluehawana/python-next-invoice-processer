#!/bin/bash

# Quick status check for invoice system
# Usage: ./check_status.sh

echo ""
echo "════════════════════════════════════════════════════════"
echo "  📊 INVOICE SYSTEM STATUS CHECK"
echo "════════════════════════════════════════════════════════"
echo ""

# Check backend
echo "🔍 Checking Backend..."
BACKEND_STATUS=$(curl -s "https://api.bluehawana.com/reconciliation-status" 2>&1)

if echo "$BACKEND_STATUS" | grep -q "records"; then
    echo "   ✅ Backend: Online and responding"
    
    # Get details
    PARTNERS=$(echo "$BACKEND_STATUS" | python3 -c "import json,sys; data=json.load(sys.stdin); print(len(data['records']))" 2>/dev/null || echo "0")
    TOTAL_FILES=$(echo "$BACKEND_STATUS" | python3 -c "import json,sys; data=json.load(sys.stdin); print(sum(len(r.get('files', [])) for r in data['records']))" 2>/dev/null || echo "0")
    
    echo "   📁 Partners tracked: $PARTNERS"
    echo "   📄 Total invoices: $TOTAL_FILES"
    echo ""
    
    # Show per-partner breakdown
    echo "   Partner Breakdown:"
    echo "$BACKEND_STATUS" | python3 << 'PYTHON'
import json, sys
try:
    data = json.load(sys.stdin)
    for r in data['records']:
        partner = r['partner']
        files = len(r.get('files', []))
        hw_count = r.get('handwritten_count', 0)
        matched = r.get('matched_count', 0)
        status = "✅" if r.get('reconciled') else ("📝" if hw_count > 0 else "⚠️")
        print(f"      {status} {partner}: {matched}/{hw_count} matched, {files} files")
except:
    pass
PYTHON
else
    echo "   ❌ Backend: Offline or not responding"
fi

echo ""
echo "🔍 Checking Frontend..."

# Try to get the frontend
FRONTEND_RESPONSE=$(curl -s -w "\n%{http_code}" "https://invoices.bluehawana.com" 2>&1)
HTTP_CODE=$(echo "$FRONTEND_RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Frontend: Online (HTTP $HTTP_CODE)"
    
    # Check what month is configured (can't easily extract from compiled JS)
    echo "   📅 To verify month, open: https://invoices.bluehawana.com"
    echo "   💡 The period shown top right is always the previous calendar month"
else
    echo "   ❌ Frontend: Issue detected (HTTP $HTTP_CODE)"
fi

echo ""
echo "🔍 Checking VPS Backend Service..."
ssh racknerd 'systemctl is-active invoice-backend' > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ VPS Service: Running"
    UPTIME=$(ssh racknerd 'systemctl status invoice-backend | grep "Active:"' 2>/dev/null | awk '{print $3, $4}')
    echo "   ⏱️  Uptime: $UPTIME"
else
    echo "   ❌ VPS Service: Not running"
    echo "   💡 Restart with: ssh racknerd 'sudo systemctl restart invoice-backend'"
fi

echo ""
echo "🔍 Checking that Mac, GitHub and VPS run the SAME code..."
cd "$(dirname "$0")"
git fetch -q origin main 2>/dev/null
LOCAL=$(git rev-parse --short HEAD)
REMOTE=$(git rev-parse --short origin/main)
VPS=$(ssh racknerd 'cd /home/harvad/invoice-processor && git rev-parse --short HEAD' 2>/dev/null)
VPS_DIRTY=$(ssh racknerd 'cd /home/harvad/invoice-processor && git status --porcelain --untracked-files=no | wc -l' 2>/dev/null | tr -d ' ')
MAC_DIRTY=$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')
echo "   Mac:    $LOCAL  (uncommitted files: $MAC_DIRTY)"
echo "   GitHub: $REMOTE"
echo "   VPS:    $VPS  (edited on server: $VPS_DIRTY)"
if [ "$LOCAL" = "$REMOTE" ] && [ "$REMOTE" = "$VPS" ] && [ "$VPS_DIRTY" = "0" ] && [ "$MAC_DIRTY" = "0" ]; then
    echo "   ✅ All three are identical"
else
    echo "   ❌ OUT OF SYNC - run ./setup_month.sh to deploy the Mac version everywhere"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo ""
echo "💡 Quick Actions:"
echo "   • Open website: open https://invoices.bluehawana.com"
echo "   • View logs: ssh racknerd 'journalctl -u invoice-backend -n 50'"
echo "   • Restart backend: ssh racknerd 'sudo systemctl restart invoice-backend'"
echo "   • Check GitHub Actions: open https://github.com/bluehawana/python-next-invoice-processer/actions"
echo ""
