#!/bin/bash
# Quick deployment script for VPS

echo "🚀 Deploying updated invoice system to VPS..."
echo ""

# Find the project directory
if [ -d "/root/python-next-invoice-processer" ]; then
    PROJECT_DIR="/root/python-next-invoice-processer"
elif [ -d "~/python-next-invoice-processer" ]; then
    PROJECT_DIR="~/python-next-invoice-processer"
elif [ -d "/home/harvad/python-next-invoice-processer" ]; then
    PROJECT_DIR="/home/harvad/python-next-invoice-processer"
else
    echo "❌ Project directory not found!"
    echo "Please run this from the project directory or specify the path"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

echo "📂 Project directory: $PROJECT_DIR"
echo ""

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    exit 1
fi

echo ""
echo "✅ Code updated successfully!"
echo ""

# Restart the service
echo "🔄 Restarting backend service..."

# Try systemd first
if systemctl is-active --quiet backend; then
    echo "   Using systemd..."
    sudo systemctl restart backend
    echo "   ✅ Service restarted"
# Try PM2
elif command -v pm2 &> /dev/null; then
    echo "   Using PM2..."
    pm2 restart backend 2>/dev/null || pm2 restart all
    echo "   ✅ PM2 restarted"
else
    echo "   ⚠️  No service manager found"
    echo "   Please restart manually:"
    echo "   cd backend && source venv/bin/activate && python main.py"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 What's new:"
echo "   • Uber invoices now show complete breakdown"
echo "   • Easy CLI tool: python backend/generate_invoices.py 2026 3"
echo "   • New API endpoints for monthly generation"
echo ""
echo "🧪 Test it:"
echo "   cd backend && source venv/bin/activate"
echo "   python generate_invoices.py 2026 3 /tmp/test"
echo ""
