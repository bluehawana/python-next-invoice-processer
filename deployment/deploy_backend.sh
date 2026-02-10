#!/bin/bash

# Configuration
SERVER_ALIAS="racknerd"
REMOTE_USER="harvad"
REMOTE_DIR="/home/harvad/invoice-processor"
DOMAIN="invoices-api.bluehawana.com"

echo "Deploying BACKEND ONLY to $SERVER_ALIAS..."

# 1. Create directory
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS "mkdir -p $REMOTE_DIR"

# 2. Sync files (excluding node_modules, venv, .git)
# We sync everything but we only care about backend really
echo "Syncing files..."
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '.git' \
    --exclude '.next' \
    ./ $SERVER_ALIAS:$REMOTE_DIR

# 3. Setup Backend
echo "Setting up Backend..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    cd $REMOTE_DIR/backend
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    ./venv/bin/pip install uvicorn fastapi playwright
    ./venv/bin/playwright install chromium
EOF

# 4. Configure System Services
echo "Configuring Services..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    # Backend Service
    sudo cp $REMOTE_DIR/deployment/backend.service /etc/systemd/system/invoice-backend.service
    sudo systemctl daemon-reload
    sudo systemctl enable invoice-backend
    sudo systemctl restart invoice-backend

    # Frontend Cleanup (Stop PM2 process if running)
    sudo npm install -g pm2
    pm2 stop invoice-frontend || true
    pm2 delete invoice-frontend || true
    pm2 save

    # Nginx for Backend API
    sudo apt-get install -y nginx
    # Use the new backend-specific config
    sudo cp $REMOTE_DIR/deployment/nginx-backend.conf /etc/nginx/sites-available/$DOMAIN
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    
    # Remove old frontend config if present
    sudo rm -f /etc/nginx/sites-available/invoices.bluehawana.com
    sudo rm -f /etc/nginx/sites-enabled/invoices.bluehawana.com
    
    sudo nginx -t && sudo systemctl restart nginx
    
    # Certbot (SSL)
    sudo apt-get install -y certbot python3-certbot-nginx
    # Attempt to obtain cert, but don't fail deployment if DNS isn't ready
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@bluehawana.com || echo "Certbot failed. Ensure DNS for $DOMAIN points to this server IP."
EOF

echo "Backend Deployment Complete!"
echo "API URL: https://$DOMAIN"
echo "Now connect your repository to Cloudflare Pages for the frontend."
