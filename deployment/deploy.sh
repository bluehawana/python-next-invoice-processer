#!/bin/bash

# Configuration
SERVER_ALIAS="racknerd"
REMOTE_USER="harvad"
REMOTE_DIR="/home/harvad/invoice-processor"
DOMAIN="invoices.bluehawana.com"

echo "Deploying to $SERVER_ALIAS..."

# 1. Create directory
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS "mkdir -p $REMOTE_DIR"

# 2. Sync files (excluding node_modules, venv, .git)
echo "Syncing files..."
rsync -avz -e "ssh -o StrictHostKeyChecking=no" --exclude 'node_modules' --exclude 'venv' --exclude '.git' --exclude '.next' ./ $SERVER_ALIAS:$REMOTE_DIR

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

# Note: Ensure requirements.txt exists!
if [ ! -f backend/requirements.txt ]; then
    echo "Creating requirements.txt..."
    # Create simple requirements.txt based on imports if missing
    cat > backend/requirements.txt << EOL
fastapi
uvicorn
python-multipart
stripe
requests
boto3
pydantic
EOL
    rsync -avz -e "ssh -o StrictHostKeyChecking=no" backend/requirements.txt $SERVER_ALIAS:$REMOTE_DIR/backend/
fi

# 4. Setup Frontend
echo "Setting up Frontend..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    cd $REMOTE_DIR/frontend
    # Install Node.js if missing (simplified check)
    if ! command -v npm &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    npm install
    
    # Build with Environment Variable
    export NEXT_PUBLIC_API_URL="https://$DOMAIN/api"
    npm run build
EOF

# 5. Configure System Services
echo "Configuring Services..."
ssh -o StrictHostKeyChecking=no $SERVER_ALIAS << EOF
    # Backend Service
    sudo cp $REMOTE_DIR/deployment/backend.service /etc/systemd/system/invoice-backend.service
    sudo systemctl daemon-reload
    sudo systemctl enable invoice-backend
    sudo systemctl restart invoice-backend

    # Frontend (PM2)
    sudo npm install -g pm2
    cd $REMOTE_DIR
    pm2 start deployment/ecosystem.config.js
    pm2 save
    pm2 startup | tail -n 1 | sudo bash

    # Nginx
    sudo apt-get install -y nginx
    sudo cp $REMOTE_DIR/deployment/nginx.conf /etc/nginx/sites-available/$DOMAIN
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl restart nginx
    
    # Certbot (SSL)
    sudo apt-get install -y certbot python3-certbot-nginx
    # Attempt to obtain cert, but don't fail deployment if DNS isn't ready
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@bluehawana.com || echo "Certbot failed, likely due to DNS not propagating yet. Run manually later."
EOF

echo "Deployment Complete! Check https://$DOMAIN"
