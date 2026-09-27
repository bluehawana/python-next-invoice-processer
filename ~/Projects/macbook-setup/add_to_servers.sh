#!/bin/bash
# Add MacBook Pro SSH key to all servers
# Run this on Mac Mini (which already has access to all servers)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔑 Adding MacBook Pro to All Servers${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if public key file exists
if [ ! -f mbp_public_key.txt ]; then
    echo -e "${RED}❌ Error: mbp_public_key.txt not found${NC}"
    echo ""
    echo "Please paste your MacBook Pro's public key:"
    read -r MBP_KEY
    echo "$MBP_KEY" > mbp_public_key.txt
else
    MBP_KEY=$(cat mbp_public_key.txt)
fi

echo -e "${YELLOW}Public key to add:${NC}"
echo "$MBP_KEY"
echo ""

# Function to add key to server
add_key_to_server() {
    local server=$1
    local name=$2
    
    echo -e "${BLUE}Adding to $name...${NC}"
    
    if echo "$MBP_KEY" | ssh "$server" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'Key added successfully'"; then
        echo -e "${GREEN}✅ Added to $name${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to add to $name${NC}"
        return 1
    fi
}

# Add to each server
echo -e "${YELLOW}Adding MacBook Pro key to all servers...${NC}"
echo ""

# RackNerd
add_key_to_server "racknerd" "RackNerd (Invoice Processor)"

# AlphaVPS
add_key_to_server "alphavps" "AlphaVPS (Main Server)"

# Tailscale - root
add_key_to_server "talpha" "Tailscale VPS (root)"

# Tailscale - admin
add_key_to_server "topen" "Tailscale VPS (admin)"

# EC2 (if accessible)
if ssh -q ec2u1 exit 2>/dev/null; then
    add_key_to_server "ec2u1" "AWS EC2"
else
    echo -e "${YELLOW}⚠️  EC2 not accessible, skipping${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ MacBook Pro added to all servers!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Test from MacBook Pro:${NC}"
echo "  ssh racknerd"
echo "  ssh talpha"
echo ""
