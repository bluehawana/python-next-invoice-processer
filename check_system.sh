#!/bin/bash

# Comprehensive system status check

echo "🔍 Invoice Processing System Status Check"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check local backend
echo "📍 LOCAL BACKEND (localhost:8000)"
echo "-----------------------------------"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
    
    # Test trigger
    echo "   Testing invoice collection trigger..."
    RESPONSE=$(curl -s -X POST "http://localhost:8000/trigger-download?year=2025&month=1")
    echo "   Response: $RESPONSE"
    
    # Wait and check status
    sleep 5
    echo "   Checking reconciliation status..."
    STATUS=$(curl -s "http://localhost:8000/reconciliation-status")
    RECORD_COUNT=$(echo $STATUS | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('records', [])))" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}Found $RECORD_COUNT reconciliation records${NC}"
else
    echo -e "${RED}❌ Backend not running${NC}"
    echo "   Start with: cd backend && ./start_server.sh"
fi

echo ""

# Check production backend
echo "🌐 PRODUCTION BACKEND (invoices-api.bluehawana.com)"
echo "---------------------------------------------------"
if curl -s https://invoices-api.bluehawana.com/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Production API is accessible${NC}"
    
    # Check status
    STATUS=$(curl -s "https://invoices-api.bluehawana.com/reconciliation-status")
    if [ ! -z "$STATUS" ]; then
        RECORD_COUNT=$(echo $STATUS | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('records', [])))" 2>/dev/null || echo "0")
        echo -e "   ${GREEN}Reconciliation records: $RECORD_COUNT${NC}"
        
        # Show config
        echo "   Service configuration:"
        echo $STATUS | python3 -c "
import sys, json
data = json.load(sys.stdin)
for service, enabled in data.get('config', {}).items():
    status = '✅' if enabled else '❌'
    print(f'      {status} {service}')
" 2>/dev/null
    fi
else
    echo -e "${RED}❌ Production API not accessible${NC}"
    echo "   Check deployment with: ./fix_production.sh"
fi

echo ""

# Check frontend
echo "🎨 FRONTEND (invoices.bluehawana.com)"
echo "--------------------------------------"
if curl -s https://invoices.bluehawana.com/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
fi

echo ""

# Check environment
echo "⚙️  ENVIRONMENT CONFIGURATION"
echo "-----------------------------"
cd backend 2>/dev/null || cd ../backend 2>/dev/null

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check key variables (without showing values)
    check_var() {
        if grep -q "^$1=" .env && ! grep -q "^$1=your_" .env && ! grep -q "^$1=$" .env; then
            echo -e "   ${GREEN}✅ $1${NC}"
        else
            echo -e "   ${RED}❌ $1 (not set or placeholder)${NC}"
        fi
    }
    
    check_var "STRIPE_API_KEY"
    check_var "EMAIL_USER"
    check_var "EMAIL_PASS"
    check_var "UBER_CLIENT_ID"
    check_var "R2_ACCESS_KEY_ID"
else
    echo -e "${RED}❌ .env file not found${NC}"
fi

echo ""

# Check dependencies
echo "📦 DEPENDENCIES"
echo "---------------"
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
    
    source venv/bin/activate 2>/dev/null
    
    check_package() {
        if python3 -c "import $1" 2>/dev/null; then
            echo -e "   ${GREEN}✅ $1${NC}"
        else
            echo -e "   ${RED}❌ $1${NC}"
        fi
    }
    
    check_package "stripe"
    check_package "boto3"
    check_package "playwright"
    check_package "fpdf"
    check_package "fastapi"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "   Create with: python3 -m venv venv"
fi

echo ""

# Check invoice storage
echo "📁 INVOICE STORAGE"
echo "------------------"
if [ -d "invoices" ]; then
    COUNT=$(ls -1 invoices/*.pdf 2>/dev/null | wc -l)
    echo -e "${GREEN}✅ Invoice directory exists${NC}"
    echo "   PDF files: $COUNT"
    
    # Show recent files
    if [ $COUNT -gt 0 ]; then
        echo "   Recent files:"
        ls -lt invoices/*.pdf 2>/dev/null | head -5 | awk '{print "      " $9}' | xargs -I {} basename {}
    fi
else
    echo -e "${YELLOW}⚠️  Invoice directory not found${NC}"
fi

echo ""
echo "=========================================="
echo "📊 SUMMARY"
echo "=========================================="

# Overall status
ISSUES=0

if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

if ! curl -s https://invoices-api.bluehawana.com/ > /dev/null 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ All systems operational!${NC}"
    echo ""
    echo "Quick commands:"
    echo "  • Collect invoices: curl -X POST 'http://localhost:8000/trigger-download?year=2025&month=1'"
    echo "  • Check status: curl 'http://localhost:8000/reconciliation-status' | python3 -m json.tool"
    echo "  • Run tests: cd backend && source venv/bin/activate && python3 test_full_workflow.py"
else
    echo -e "${YELLOW}⚠️  $ISSUES issue(s) detected${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  • Start local backend: cd backend && ./start_server.sh"
    echo "  • Fix production: ./fix_production.sh"
    echo "  • Run diagnostics: cd backend && source venv/bin/activate && python3 test_workflow.py"
fi

echo ""
