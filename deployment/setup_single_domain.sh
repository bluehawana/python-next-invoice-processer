#!/bin/bash

# Setup script for single domain configuration
# Backend API accessible at: invoices.bluehawana.com/api/*
# Frontend served by Cloudflare Pages at: invoices.bluehawana.com

SERVER_ALIAS="racknerd"
REMOTE_USER="harvad"
REMOTE_DIR="/home/harvad/invoice-processor"
DOMAIN="invoices.bluehawana.com"

echo "🔧 Setting up single domain configuration for $DOMAIN"
echo "=================================================="
echo ""

echo "📋 Configuration:"
echo "   Frontend: Cloudflare Pages → $DOMAIN"
echo "   Backend:  VPS Nginx → $DOMAIN/api/*"
echo ""

# 1. Deploy backend code
echo "1️⃣  Syncing backend files..."
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '.git' \
    --exclude '.next' \
    --exclude 'frontend/out' \
    --exclude 'frontend/node_modules' \
    ./backend/ $SERVER_ALIAS:$REMOTE_DIR/backend/

echo ""
echo "2️⃣  Installing backend dependencies..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << 'EOF'
    cd /home/harvad/invoice-processor/backend
    
    # Create venv if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Install dependencies
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    # Install playwright if needed
    if ! playwright --version &> /dev/null; then
        playwright install chromium
    fi
EOF

echo ""
echo "3️⃣  Configuring nginx for single domain..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    # Copy nginx config
    sudo cp $REMOTE_DIR/deployment/nginx-single-domain.conf /etc/nginx/sites-available/$DOMAIN
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    
    # Remove old configs if they exist
    sudo rm -f /etc/nginx/sites-enabled/invoices-api.bluehawana.com
    sudo rm -f /etc/nginx/sites-available/invoices-api.bluehawana.com
    
    # Test nginx config
    sudo nginx -t
    
    # Reload nginx
    sudo systemctl reload nginx
EOF

echo ""
echo "4️⃣  Setting up backend systemd service..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    # Copy service file
    sudo cp $REMOTE_DIR/deployment/backend.service /etc/systemd/system/invoice-backend.service
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable and restart service
    sudo systemctl enable invoice-backend
    sudo systemctl restart invoice-backend
    
    # Check status
    sleep 2
    sudo systemctl status invoice-backend --no-pager | head -15
EOF

echo ""
echo "5️⃣  Setting up SSL certificate..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Get/renew certificate
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@bluehawana.com --redirect || echo "⚠️  Certbot failed. You may need to run it manually."
EOF

echo ""
echo "=================================================="
echo "✅ Backend setup complete!"
echo ""
echo "📊 Configuration Summary:"
echo "   Domain: $DOMAIN"
echo "   Frontend: Cloudflare Pages (automatic)"
echo "   Backend API: $DOMAIN/api/*"
echo "   Backend Health: $DOMAIN/api/ or $DOMAIN/health"
echo ""
echo "🧪 Test the setup:"
echo "   curl https://$DOMAIN/api/"
echo "   # Should return: {\"status\":\"Invoice Processor API is running\"}"
echo ""
echo "📝 Next steps:"
echo "   1. Update Cloudflare Pages environment variable:"
echo "      NEXT_PUBLIC_API_URL=https://$DOMAIN/api"
echo ""
echo "   2. Rebuild and deploy frontend:"
echo "      cd frontend && npm run build"
echo "      git add . && git commit -m 'Update API URL' && git push"
echo ""
echo "   3. Test the full system:"
echo "      Visit https://$DOMAIN"
echo ""
