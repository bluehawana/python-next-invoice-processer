# MacBook Pro M5 Max Setup Guide

## ✅ Done on Mac Mini

1. ✅ Created private repo: https://github.com/bluehawana/macsharing-settings
2. ✅ Added all setup scripts and configurations
3. ✅ Pushed to GitHub

## 📱 On Your MacBook Pro

### Step 1: Clone the setup repo

```bash
cd ~/Projects
git clone https://github.com/bluehawana/macsharing-settings.git
cd macsharing-settings
```

### Step 2: Run the setup script

```bash
bash setup.sh
```

This will:
- Generate SSH key for MacBook Pro
- Install Homebrew and essential tools
- Setup Git configuration
- Clone all your project repos
- Create SSH config for all servers

### Step 3: Copy your public key

After setup completes, you'll see your public key. Copy it!

```bash
cat mbp_public_key.txt
```

## 🔑 On Mac Mini (to add MBP to servers)

### Step 1: Pull the repo

```bash
cd ~/Projects/macsharing-settings
git pull
```

### Step 2: Add MacBook Pro's public key

Paste the public key from MacBook Pro into `mbp_public_key.txt`:

```bash
# Paste the key you copied from MacBook Pro
nano mbp_public_key.txt
```

### Step 3: Run the add script

```bash
bash add_to_servers.sh
```

This will add your MacBook Pro's SSH key to:
- RackNerd
- AlphaVPS
- Tailscale VPS (root)
- Tailscale VPS (admin)

## 🧪 Test on MacBook Pro

```bash
# Test RackNerd
ssh racknerd "echo 'RackNerd works!'"

# Test AlphaVPS (may not work from office)
ssh alphavps "echo 'AlphaVPS works!'"

# Test Tailscale (works from anywhere!)
ssh talpha "echo 'Tailscale works!'"
```

## 🌐 Setup Tailscale (for office access)

On MacBook Pro:

```bash
sudo tailscale up
```

Follow the authentication link in your browser.

Now you can use `ssh talpha` from anywhere, including office!

## 📂 Your Projects

All repos will be cloned to `~/Projects/`:
- python-next-invoice-processer
- (add more in repos.txt)

## 🎯 Quick Reference

### From Office (network blocks AlphaVPS):
```bash
ssh talpha  # Use Tailscale!
ssh racknerd  # Direct connection works
```

### From Home:
```bash
ssh alphavps  # Direct connection
ssh racknerd  # Direct connection
ssh talpha  # Also works
```

## 🔧 Troubleshooting

### Can't connect to AlphaVPS from office
- **Solution:** Use `ssh talpha` (Tailscale)
- Tailscale bypasses firewall restrictions

### Permission denied
- Make sure you ran `add_to_servers.sh` from Mac Mini
- Check the key was added: `ssh server "cat ~/.ssh/authorized_keys"`

### Repo clone failed
- Check GitHub authentication
- Run: `gh auth login` (GitHub CLI)

## 📝 Summary

1. ✅ On MacBook Pro: `bash setup.sh`
2. ✅ Copy public key from `mbp_public_key.txt`
3. ✅ On Mac Mini: Paste key and run `bash add_to_servers.sh`
4. ✅ On MacBook Pro: `sudo tailscale up`
5. ✅ Test: `ssh racknerd`, `ssh talpha`

🎉 Done! Your MacBook Pro is now fully configured!
