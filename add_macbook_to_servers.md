# Add MacBook Pro M5 Max to Server Whitelist

## Step 1: Generate SSH Key on MacBook Pro

On your **MacBook Pro**, run:

```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "harvad@macbookpro-m5max" -f ~/.ssh/id_ed25519_mbp

# Display the public key
cat ~/.ssh/id_ed25519_mbp.pub
```

Copy the entire output (starts with `ssh-ed25519 AAAA...`)

## Step 2: Add Key to Each Server

### Option A: From Mac Mini (Easiest)

Since your Mac Mini already has access, use it to add the MacBook Pro key:

```bash
# On Mac Mini, save MacBook Pro's public key
echo "ssh-ed25519 AAAA... harvad@macbookpro-m5max" > /tmp/mbp_key.pub

# Add to RackNerd
ssh racknerd "cat >> ~/.ssh/authorized_keys" < /tmp/mbp_key.pub

# Add to AlphaVPS
ssh alphavps "cat >> ~/.ssh/authorized_keys" < /tmp/mbp_key.pub

# Add to EC2
ssh ec2u1 "cat >> ~/.ssh/authorized_keys" < /tmp/mbp_key.pub

# Add to Tailscale VPS (root)
ssh talpha "cat >> ~/.ssh/authorized_keys" < /tmp/mbp_key.pub

# Add to Tailscale VPS (admin user)
ssh topen "cat >> ~/.ssh/authorized_keys" < /tmp/mbp_key.pub
```

### Option B: Manually on Each Server

If you can access servers directly (e.g., via password or console):

**On RackNerd:**
```bash
ssh harvad@107.175.235.220
echo "ssh-ed25519 AAAA... harvad@macbookpro-m5max" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
exit
```

**On AlphaVPS:**
```bash
ssh -p 1025 harvad@94.72.141.71
echo "ssh-ed25519 AAAA... harvad@macbookpro-m5max" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
exit
```

## Step 3: Update SSH Config on MacBook Pro

Create `~/.ssh/config` on MacBook Pro:

```bash
cat > ~/.ssh/config << 'EOF'
# RackNerd - Invoice processor
Host racknerd
  HostName 107.175.235.220
  User harvad
  Port 22
  IdentityFile ~/.ssh/id_ed25519_mbp
  ServerAliveInterval 60
  ServerAliveCountMax 3

# AlphaVPS - Main server (may not work from office)
Host alphavps
  HostName 94.72.141.71
  User harvad
  Port 1025
  IdentityFile ~/.ssh/id_ed25519_mbp
  ServerAliveInterval 60
  ServerAliveCountMax 3

# Tailscale VPS - Works from anywhere (including office!)
Host talpha
  HostName 100.120.173.48
  User root
  IdentityFile ~/.ssh/id_ed25519_mbp
  ServerAliveInterval 60
  ServerAliveCountMax 3

# Tailscale VPS - Admin user
Host topen
  HostName 100.120.173.48
  User admin
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
EOF

chmod 600 ~/.ssh/config
```

## Step 4: Test Connections from MacBook Pro

```bash
# Test RackNerd
ssh racknerd "echo 'RackNerd connection works!'"

# Test AlphaVPS (may fail from office network)
ssh alphavps "echo 'AlphaVPS connection works!'"

# Test Tailscale (should work from anywhere)
ssh talpha "echo 'Tailscale connection works!'"
```

## Step 5: Setup Tailscale for Office Access

Since your office network blocks AlphaVPS, use Tailscale:

**On MacBook Pro:**
```bash
# Install Tailscale
brew install tailscale

# Start Tailscale
sudo tailscale up

# Follow the authentication link in browser
```

**On AlphaVPS (if not already setup):**
```bash
ssh alphavps  # From home or Mac Mini
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Now you can use `ssh talpha` from anywhere, including office!

## Quick Setup Script

Run this on your **Mac Mini** to add MacBook Pro to all servers:

```bash
#!/bin/bash
# Add MacBook Pro key to all servers

# Get the MacBook Pro public key (paste it here)
MBP_KEY="ssh-ed25519 AAAA... harvad@macbookpro-m5max"

echo "Adding MacBook Pro to all servers..."

# RackNerd
echo "$MBP_KEY" | ssh racknerd "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo "✅ Added to RackNerd"

# AlphaVPS
echo "$MBP_KEY" | ssh alphavps "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo "✅ Added to AlphaVPS"

# Tailscale (root)
echo "$MBP_KEY" | ssh talpha "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo "✅ Added to Tailscale (root)"

# Tailscale (admin)
echo "$MBP_KEY" | ssh topen "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo "✅ Added to Tailscale (admin)"

echo ""
echo "🎉 MacBook Pro added to all servers!"
echo "Test from MacBook Pro: ssh racknerd"
```

## Troubleshooting

### Can't connect from office to AlphaVPS
- **Solution:** Use Tailscale! `ssh talpha` instead of `ssh alphavps`
- Tailscale creates a VPN mesh network that bypasses firewall restrictions

### Permission denied (publickey)
- Check key was added: `ssh server "cat ~/.ssh/authorized_keys"`
- Check permissions: `chmod 600 ~/.ssh/id_ed25519_mbp`
- Check SSH config: `cat ~/.ssh/config`

### Connection timeout
- Office firewall may block port 1025 (AlphaVPS)
- Use Tailscale as workaround
- Or use VPN/proxy

## Summary

1. ✅ Generate SSH key on MacBook Pro
2. ✅ Add key to all servers (via Mac Mini)
3. ✅ Setup SSH config on MacBook Pro
4. ✅ Install Tailscale for office access
5. ✅ Test connections

**From Office:** Use `ssh talpha` (Tailscale) instead of `ssh alphavps`
**From Home:** Both work!
