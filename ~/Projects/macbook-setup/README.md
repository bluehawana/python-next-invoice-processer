# MacBook Pro M5 Max Setup

Private repository for setting up new MacBook Pro with all configurations, SSH keys, and project settings.

## 🚀 Quick Start

On your **MacBook Pro**, run:

```bash
# Clone this repo
cd ~/Projects
git clone https://github.com/bluehawana/macbook-setup.git
cd macbook-setup

# Run the setup script
bash setup.sh
```

## 📋 What This Does

1. ✅ Generates SSH key for MacBook Pro
2. ✅ Creates SSH config for all servers
3. ✅ Sets up Git configuration
4. ✅ Installs essential tools (Homebrew, Python, Node, etc.)
5. ✅ Clones all your project repositories
6. ✅ Sets up Tailscale for office access

## 🔑 Adding MacBook Pro to Servers

After running `setup.sh`, you'll get your public key. Then:

**From Mac Mini** (which already has access):
```bash
cd ~/Projects/macbook-setup
bash add_to_servers.sh
```

This will add your MacBook Pro's SSH key to all servers.

## 📂 Repository Structure

```
macbook-setup/
├── README.md                    # This file
├── setup.sh                     # Main setup script for MacBook Pro
├── add_to_servers.sh           # Script to add MBP key to all servers (run from Mac Mini)
├── ssh_config                   # SSH configuration template
├── gitconfig                    # Git configuration
├── repos.txt                    # List of repositories to clone
├── brew_packages.txt           # Homebrew packages to install
└── docs/
    ├── SSH_SETUP.md            # Detailed SSH setup guide
    ├── TAILSCALE_SETUP.md      # Tailscale configuration
    └── TROUBLESHOOTING.md      # Common issues and solutions
```

## 🌐 Office Network Access

Your office network blocks AlphaVPS (port 1025). Solution:

**Use Tailscale:**
- `ssh talpha` - Works from anywhere (office, home, travel)
- `ssh alphavps` - Only works from home

## 📝 Server List

- **racknerd** - Invoice processor (107.175.235.220:22)
- **alphavps** - Main server (94.72.141.71:1025) - Blocked at office
- **talpha** - AlphaVPS via Tailscale (100.120.173.48) - Works everywhere
- **topen** - Tailscale admin workspace
- **ec2u1** - AWS EC2 instance

## 🔧 Manual Steps

If automatic setup fails:

1. Generate SSH key: `ssh-keygen -t ed25519 -C "harvad@macbookpro-m5max" -f ~/.ssh/id_ed25519_mbp`
2. Copy public key: `cat ~/.ssh/id_ed25519_mbp.pub`
3. Add to servers: See `docs/SSH_SETUP.md`

## 📦 Projects to Clone

All your repositories are listed in `repos.txt` and will be cloned automatically to `~/Projects/`

## 🆘 Troubleshooting

See `docs/TROUBLESHOOTING.md` for common issues.

## 🔒 Security Note

This is a **PRIVATE** repository. Never make it public as it contains:
- Server hostnames and IPs
- SSH configuration
- Project structure

## 📞 Support

If you have issues, check the docs folder or refer to the original Mac Mini setup.
