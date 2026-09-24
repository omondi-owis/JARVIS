#!/bin/bash
# J.A.R.V.I.S. Install Script for Ubuntu Server
# Owner: Raphael
# Follows least privilege principle

set -e

echo "=== J.A.R.V.I.S. Installation ==="
echo "Owner: Raphael"
echo "Target: Ubuntu Server"

# 1. System checks
echo "[1/7] Checking system..."
if [[ $EUID -eq 0 ]]; then
   echo "Do NOT run as root. Run as sysadmin user with sudo privileges."
   exit 1
fi

# 2. Create user (if not exists)
if ! id "jarvis" &>/dev/null; then
    echo "[2/7] Creating jarvis service user..."
    sudo useradd -r -s /bin/false -d /home/sysadmin/jarvis jarvis || true
    sudo usermod -aG jarvis $USER
else
    echo "[2/7] jarvis user exists"
fi

# 3. Python venv
echo "[3/7] Creating venv..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Config from example
echo "[4/7] Setting up config..."
if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "Created config/config.json from example - EDIT IT"
fi
if [ ! -f config/device_registry.json ]; then
    cp config/device_registry.example.json config/device_registry.json
    echo "Created device_registry.json - REGISTER YOUR DEVICES"
fi
mkdir -p logs
touch logs/.gitkeep
touch logs/audit.jsonl
chmod 600 logs/audit.jsonl

# 5. .env for secrets - NEVER commit
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# J.A.R.V.I.S. Secrets - NEVER COMMIT THIS FILE
# Store in secrets manager in production
WAZUH_API_URL=
WAZUH_API_USER=
WAZUH_API_PASS=
MLINZIOPS_API_URL=
MLINZIOPS_API_KEY=
TELEPHONY_PROVIDER=
# TAILSCALE_AUTHKEY=
EOF
    chmod 600 .env
    echo "Created .env with 600 perms - ADD YOUR SECRETS"
fi

# 6. Permissions
echo "[5/7] Setting permissions..."
chmod 700 config/
chmod 600 config/*.json || true
chmod +x main.py

# 7. Systemd (optional)
echo "[6/7] Systemd service available at systemd/jarvis.service"
echo "To install: sudo cp systemd/jarvis.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now jarvis"

# 8. Verify
echo "[7/7] Verifying..."
.venv/bin/python main.py status || true

echo ""
echo "=== Installation Complete ==="
echo "Next:"
echo "1. Edit config/config.json"
echo "2. Edit .env with secrets (600 perms)"
echo "3. Run: source .venv/bin/activate && python main.py status"
echo "4. For voice: configure voice interface"
echo "Security: Never commit .env, *.key, config.json with secrets"
