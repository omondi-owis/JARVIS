#!/bin/bash
# J.A.R.V.I.S. Production Setup - Ubuntu Server
# Owner: Raphael
# Implements least privilege, hardening, Tailscale, secrets

set -e

echo "=== J.A.R.V.I.S. Production Setup ==="
echo "Owner: Raphael"
echo "Environment: Production"
echo ""

if [[ $EUID -eq 0 ]]; then
   echo "Do NOT run as root. Run as sysadmin with sudo."
   exit 1
fi

# 1. System update
echo "[1/10] Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
echo "[2/10] Installing dependencies..."
sudo apt install -y python3.11 python3.11-venv python3-pip curl git ufw fail2ban jq

# 3. Harden SSH (backup first)
echo "[3/10] Checking SSH hardening..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d) || true
echo "Current SSH config:"
grep -E "^PermitRootLogin|^PasswordAuthentication|^Port" /etc/ssh/sshd_config || true

# 4. UFW
echo "[4/10] Configuring UFW..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Allow Tailscale
sudo ufw allow in on tailscale0 || true
sudo ufw --force enable
sudo ufw status verbose

# 5. Fail2ban
echo "[5/10] Configuring Fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status || true

# 6. Create jarvis user
echo "[6/10] Creating jarvis service user..."
if ! id "jarvis" &>/dev/null; then
    sudo useradd -r -s /bin/false -d /home/sysadmin/jarvis jarvis
fi
sudo usermod -aG jarvis $USER || true

# 7. Python venv
echo "[7/10] Setting up Python venv..."
if [ ! -d .venv ]; then
    python3.11 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt || pip install -r requirements.txt

# 8. Config and secrets
echo "[8/10] Setting up config and secrets..."
mkdir -p config logs

if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "Created config/config.json - EDIT IT for production"
fi

if [ ! -f config/device_registry.json ]; then
    cp config/device_registry.example.json config/device_registry.json
    echo "Created device_registry.json - REGISTER DEVICES"
fi

if [ ! -f .env ]; then
    cp .env.example .env
    chmod 600 .env
    echo "Created .env with 600 perms - ADD SECRETS NOW"
    echo "Generate JWT secret: openssl rand -base64 32"
    echo "Then edit .env: nano .env"
else
    chmod 600 .env
fi

touch logs/.gitkeep
touch logs/audit.jsonl
chmod 600 logs/audit.jsonl || true
chmod 700 config

# 9. Tailscale (optional but recommended)
echo "[9/10] Tailscale setup (recommended for secure remote access)..."
if ! command -v tailscale &> /dev/null; then
    echo "Tailscale not installed. Install with:"
    echo "curl -fsSL https://tailscale.com/install.sh | sh"
    echo "Then: sudo tailscale up --authkey=\$TAILSCALE_AUTHKEY"
else
    echo "Tailscale installed: $(tailscale version)"
    tailscale status || true
fi

# 10. Systemd
echo "[10/10] Systemd service..."
echo "To install service:"
echo "sudo cp systemd/jarvis.service /etc/systemd/system/"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable --now jarvis"
echo "sudo systemctl status jarvis"

echo ""
echo "=== Production Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env with secrets: nano .env (600 perms)"
echo "2. Generate JWT: openssl rand -base64 32"
echo "3. Edit config/config.json and device_registry.json"
echo "4. Test: source .venv/bin/activate && python main.py status"
echo "5. Test API: python api.py or uvicorn api:app --host 127.0.0.1 --port 8000"
echo "6. Docker: docker-compose up -d (binds to 127.0.0.1:8000, expose via Tailscale)"
echo "7. Backup: ./scripts/backup.sh"
echo ""
echo "Security reminders:"
echo "- Never expose 8000 directly to public internet - use Tailscale"
echo "- .env has 600 perms, never commit"
echo "- Audit logs at logs/audit.jsonl"
echo "- Revoke device immediately if compromised: python main.py -> registry.revoke_device()"
