#!/bin/bash
# MacBook Pro M5 Max Setup Script
# Run this on your NEW MacBook Pro

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 MacBook Pro M5 Max Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. Setup SSH
echo -e "${BLUE}🔑 Step 1: Setting up SSH...${NC}"
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Generate SSH key
if [ ! -f ~/.ssh/id_ed25519_mbp ]; then
    echo -e "${YELLOW}Generating SSH key...${NC}"
    ssh-keygen -t ed25519 -C "harvad@macbookpro-m5max" -f ~/.ssh/id_ed25519_mbp -N ""
    echo -e "${GREEN}✅ SSH key generated${NC}"
else
    echo -e "${GREEN}✅ SSH key already exists${NC}"
fi

# Copy SSH config
echo -e "${YELLOW}Creating SSH config...${NC}"
cp ssh_config ~/.ssh/config
chmod 600 ~/.ssh/config
echo -e "${GREEN}✅ SSH config created${NC}"

# 2. Display public key
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🔑 YOUR PUBLIC KEY (save this!)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat ~/.ssh/id_ed25519_mbp.pub
echo ""
echo -e "${YELLOW}Copy this key and run 'bash add_to_servers.sh' on Mac Mini${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Save key to file for easy access
cat ~/.ssh/id_ed25519_mbp.pub > mbp_public_key.txt
echo -e "${GREEN}✅ Public key saved to: mbp_public_key.txt${NC}"
echo ""

# 3. Setup Git
echo -e "${BLUE}🔧 Step 2: Configuring Git...${NC}"
git config --global user.name "Harvad Lee"
git config --global user.email "hongyanab@gmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
echo -e "${GREEN}✅ Git configured${NC}"

# 4. Install Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${BLUE}🍺 Step 3: Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add to PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    
    echo -e "${GREEN}✅ Homebrew installed${NC}"
else
    echo -e "${GREEN}✅ Homebrew already installed${NC}"
fi

# 5. Install packages
echo -e "${BLUE}📦 Step 4: Installing packages...${NC}"
if [ -f brew_packages.txt ]; then
    while IFS= read -r package; do
        if ! brew list "$package" &> /dev/null; then
            echo -e "${YELLOW}Installing $package...${NC}"
            brew install "$package"
        else
            echo -e "${GREEN}✅ $package already installed${NC}"
        fi
    done < brew_packages.txt
fi

# 6. Setup Projects directory
echo -e "${BLUE}📂 Step 5: Setting up Projects directory...${NC}"
mkdir -p ~/Projects
cd ~/Projects

# 7. Clone repositories
echo -e "${BLUE}📦 Step 6: Cloning repositories...${NC}"
if [ -f ~/Projects/macbook-setup/repos.txt ]; then
    while IFS= read -r repo; do
        # Skip empty lines and comments
        [[ -z "$repo" || "$repo" =~ ^# ]] && continue
        
        repo_name=$(basename "$repo" .git)
        if [ ! -d "$repo_name" ]; then
            echo -e "${YELLOW}Cloning $repo_name...${NC}"
            git clone "$repo" || echo -e "${RED}Failed to clone $repo_name${NC}"
        else
            echo -e "${GREEN}✅ $repo_name already exists${NC}"
        fi
    done < ~/Projects/macbook-setup/repos.txt
fi

# 8. Setup Tailscale
echo ""
echo -e "${BLUE}🌐 Step 7: Tailscale setup${NC}"
if ! command -v tailscale &> /dev/null; then
    echo -e "${YELLOW}Tailscale not installed. Installing...${NC}"
    brew install tailscale
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🌐 IMPORTANT: Setup Tailscale for office access${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Run: sudo tailscale up${NC}"
echo -e "${BLUE}Then you can use 'ssh talpha' from anywhere (including office!)${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 9. Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Add SSH key to servers:${NC}"
echo "   - Your public key is in: mbp_public_key.txt"
echo "   - On Mac Mini, run: bash add_to_servers.sh"
echo ""
echo "2. ${YELLOW}Setup Tailscale:${NC}"
echo "   sudo tailscale up"
echo ""
echo "3. ${YELLOW}Test SSH connections:${NC}"
echo "   ssh racknerd"
echo "   ssh talpha  # Works from office!"
echo ""
echo "4. ${YELLOW}Start working:${NC}"
echo "   cd ~/Projects/python-next-invoice-processer"
echo ""
echo -e "${GREEN}🎉 Your MacBook Pro is ready!${NC}"
echo ""
