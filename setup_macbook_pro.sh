#!/bin/bash
# Setup script for new MacBook Pro
# This will sync all SSH configs, keys, and project settings

set -e

echo "🚀 Setting up MacBook Pro with all configurations..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Setup SSH directory
echo -e "${BLUE}📁 Setting up SSH configuration...${NC}"
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 2. Generate new SSH key for MacBook Pro (if not exists)
if [ ! -f ~/.ssh/id_ed25519_mbp ]; then
    echo -e "${YELLOW}🔑 Generating new SSH key for MacBook Pro...${NC}"
    ssh-keygen -t ed25519 -C "harvad@macbookpro" -f ~/.ssh/id_ed25519_mbp -N ""
    echo -e "${GREEN}✅ SSH key generated: ~/.ssh/id_ed25519_mbp${NC}"
else
    echo -e "${GREEN}✅ SSH key already exists${NC}"
fi

# 3. Create SSH config
echo -e "${BLUE}📝 Creating SSH config...${NC}"
cat > ~/.ssh/config << 'EOF'
# AlphaVPS - Main server
Host alphavps
  HostName 94.72.141.71
  User harvad
  Port 1025
  IdentityFile ~/.ssh/id_ed25519_mbp
  ServerAliveInterval 60
  ServerAliveCountMax 3
  # Add these if office network blocks it
  # ProxyCommand nc -X connect -x proxy.example.com:8080 %h %p

# RackNerd - Invoice processor
Host racknerd
  HostName 107.175.235.220
  User harvad
  Port 22
  IdentityFile ~/.ssh/id_ed25519_mbp
  ServerAliveInterval 60
  ServerAliveCountMax 3

# AWS EC2
Host ec2u1
  HostName ec2-51-20-31-28.eu-north-1.compute.amazonaws.com
  User ubuntu
  IdentityFile ~/.ssh/clawone26.pem
  ServerAliveInterval 60
  ServerAliveCountMax 3

# Tailscale VPS - Root access
Host talpha
  HostName 100.120.173.48
  User root
  IdentityFile ~/.ssh/id_ed25519_mbp
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  ServerAliveInterval 60
  ServerAliveCountMax 3

# Tailscale VPS - Admin workspace
Host topen
  HostName 100.120.173.48
  User admin
  IdentityFile ~/.ssh/id_ed25519_mbp
  ServerAliveInterval 60
  ServerAliveCountMax 3
EOF

chmod 600 ~/.ssh/config
echo -e "${GREEN}✅ SSH config created${NC}"

# 4. Display public key to add to servers
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🔑 IMPORTANT: Add this public key to your servers${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
cat ~/.ssh/id_ed25519_mbp.pub
echo ""
echo -e "${YELLOW}Run this on each server:${NC}"
echo -e "${BLUE}echo '$(cat ~/.ssh/id_ed25519_mbp.pub)' >> ~/.ssh/authorized_keys${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 5. Setup Projects directory
echo -e "${BLUE}📂 Setting up Projects directory...${NC}"
mkdir -p ~/Projects
cd ~/Projects

# 6. Clone repositories (if not already cloned)
echo -e "${BLUE}📦 Cloning repositories...${NC}"

repos=(
    "https://github.com/bluehawana/python-next-invoice-processer.git"
    # Add more repos here as needed
)

for repo in "${repos[@]}"; do
    repo_name=$(basename "$repo" .git)
    if [ ! -d "$repo_name" ]; then
        echo -e "${YELLOW}Cloning $repo_name...${NC}"
        git clone "$repo"
        echo -e "${GREEN}✅ Cloned $repo_name${NC}"
    else
        echo -e "${GREEN}✅ $repo_name already exists${NC}"
    fi
done

# 7. Setup Git config
echo -e "${BLUE}⚙️  Configuring Git...${NC}"
git config --global user.name "Harvad Lee"
git config --global user.email "hongyanab@gmail.com"
git config --global init.defaultBranch main
echo -e "${GREEN}✅ Git configured${NC}"

# 8. Install Homebrew (if not installed)
if ! command -v brew &> /dev/null; then
    echo -e "${BLUE}🍺 Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo -e "${GREEN}✅ Homebrew installed${NC}"
else
    echo -e "${GREEN}✅ Homebrew already installed${NC}"
fi

# 9. Install essential tools
echo -e "${BLUE}🔧 Installing essential tools...${NC}"
brew_packages=(
    "git"
    "python@3.11"
    "node"
    "wget"
    "curl"
    "jq"
    "tailscale"
)

for package in "${brew_packages[@]}"; do
    if ! brew list "$package" &> /dev/null; then
        echo -e "${YELLOW}Installing $package...${NC}"
        brew install "$package"
    else
        echo -e "${GREEN}✅ $package already installed${NC}"
    fi
done

# 10. Setup Tailscale (for VPS access from office)
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🌐 IMPORTANT: Setup Tailscale for office access${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Tailscale allows you to access AlphaVPS even from office network${NC}"
echo ""
echo -e "${YELLOW}Steps:${NC}"
echo "1. Run: sudo tailscale up"
echo "2. Follow the authentication link"
echo "3. Then you can use: ssh talpha (instead of ssh alphavps)"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 11. Create sync script
echo -e "${BLUE}📋 Creating sync script...${NC}"
cat > ~/sync_projects.sh << 'SYNCEOF'
#!/bin/bash
# Sync all projects from Mac Mini to MacBook Pro

echo "🔄 Syncing projects from Mac Mini..."

# Sync via rsync over SSH
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '.next' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    harvadlee@macmini.local:~/Projects/ ~/Projects/

echo "✅ Sync complete!"
SYNCEOF

chmod +x ~/sync_projects.sh
echo -e "${GREEN}✅ Sync script created: ~/sync_projects.sh${NC}"

# 12. Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "1. Add your SSH public key to servers:"
echo "   cat ~/.ssh/id_ed25519_mbp.pub"
echo ""
echo "2. Test SSH connections:"
echo "   ssh racknerd"
echo "   ssh alphavps  # May not work from office"
echo ""
echo "3. Setup Tailscale for office access:"
echo "   sudo tailscale up"
echo "   ssh talpha  # Works from anywhere!"
echo ""
echo "4. Sync projects from Mac Mini:"
echo "   ~/sync_projects.sh"
echo ""
echo -e "${YELLOW}💡 Tip: Use 'talpha' instead of 'alphavps' when at office${NC}"
echo ""
