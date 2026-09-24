#!/bin/bash
# Tailscale Secure Remote Access Setup for JARVIS
# Recommended: Avoid exposing admin services directly to public internet

set -e

echo "=== Tailscale Setup for J.A.R.V.I.S. ==="

if [[ $EUID -ne 0 ]]; then
   echo "Run with sudo for Tailscale install"
   exit 1
fi

# Install Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "Tailscale already installed: $(tailscale version)"
fi

# Check auth key
if [ -z "$TAILSCALE_AUTHKEY" ]; then
    if [ -f /home/sysadmin/jarvis/.env ]; then
        source /home/sysadmin/jarvis/.env
    fi
fi

if [ -z "$TAILSCALE_AUTHKEY" ]; then
    echo "TAILSCALE_AUTHKEY not set. Get from https://login.tailscale.com/admin/settings/keys"
    echo "Generate reusable key, then:"
    echo "export TAILSCALE_AUTHKEY=tskey-auth-..."
    echo "sudo -E ./scripts/tailscale_setup.sh"
    exit 1
fi

echo "Bringing up Tailscale..."
tailscale up --authkey=$TAILSCALE_AUTHKEY --ssh --advertise-tags=tag:jarvis

echo "Tailscale status:"
tailscale status
tailscale ip -4

echo ""
echo "=== Tailscale Setup Complete ==="
echo "Your JARVIS API at 127.0.0.1:8000 is now accessible via Tailscale IP"
echo "Tailscale IP: $(tailscale ip -4)"
echo "Access: http://$(tailscale ip -4):8000/health (if you bind to 0.0.0.0) or via SSH"
echo "Better: Keep bound to 127.0.0.1 and use 'tailscale serve' or SSH port forward"
echo ""
echo "For secure serve:"
echo "sudo tailscale serve --bg --https=443 http://127.0.0.1:8000"
