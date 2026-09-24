# J.A.R.V.I.S. Deployment - Production

## Ubuntu Server Production Setup

### Prerequisites
- Ubuntu 22.04 LTS or 24.04 LTS
- User `sysadmin` with sudo (not root)
- SSH key auth only, no password auth
- Domain or Tailscale tailnet

### 1. Clone Repo (as sysadmin)

```bash
ssh sysadmin@YOUR_SERVER
cd ~
git clone git@github.com:omondi-owis/JARVIS.git jarvis
cd jarvis
```

### 2. Production Setup Script

```bash
chmod +x scripts/production_setup.sh
./scripts/production_setup.sh
```

This will:
- Update system
- Install Python 3.11, UFW, fail2ban
- Configure UFW (deny incoming, allow 22,80,443, tailscale0)
- Enable fail2ban
- Create jarvis service user
- Create venv and install prod requirements
- Create config from examples, .env with 600 perms
- Check Tailscale

### 3. Configure Secrets

```bash
nano .env
# Set:
# JWT_SECRET=$(openssl rand -base64 32)
# WAZUH_API_URL, WAZUH_API_USER, WAZUH_API_PASS
# MLINZIOPS_API_URL, MLINZIOPS_API_KEY
# TWILIO_*
# MQTT_*
# TAILSCALE_AUTHKEY

chmod 600 .env
```

### 4. Configure Device Registry

```bash
nano config/device_registry.json
# Register your devices:
# ubuntu-prod-01, sec-lab-kali, windows workstation, etc.
# Set trust_status trusted, revocation_status active

nano config/config.json
# Set integrations enabled true/false
```

### 5. Tailscale (Recommended)

```bash
# Get auth key from https://login.tailscale.com/admin/settings/keys
export TAILSCALE_AUTHKEY=tskey-auth-xxxx
sudo -E ./scripts/tailscale_setup.sh

# Or manually:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY --ssh

# Serve API securely via Tailscale (keeps 127.0.0.1 binding)
sudo tailscale serve --bg --https=443 http://127.0.0.1:8000
```

### 6. Test

```bash
source .venv/bin/activate
python main.py status
python main.py hardening-report
python main.py devices

# API
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
# In another terminal:
curl http://127.0.0.1:8000/health
```

### 7. Systemd Service

```bash
sudo cp systemd/jarvis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis
sudo systemctl status jarvis
sudo journalctl -u jarvis -f
```

### 8. Docker (Alternative)

```bash
docker-compose up -d --build
docker-compose logs -f jarvis
# API at 127.0.0.1:8000 (not public, use Tailscale)
```

### 9. Backup

```bash
./scripts/backup.sh
# Backups to /home/sysadmin/backups/jarvis/
# Encrypt .env separately: gpg --symmetric --cipher-algo AES256 .env
```

## GitHub Push Workflow

On Ubuntu server after updating framework:

```bash
cd ~/jarvis
git status
# Ensure .env, *.key, config.json NOT in status (gitignored)

git add .
git commit -m "feat: production hardening, Tailscale, full Wazuh/MlinziOps, telephony, IoT, monitoring"

git push origin main
```

From Arena sandbox (this environment):
- Download `jarvis-framework.tar.gz`
- SCP to Ubuntu: `scp jarvis-framework.tar.gz sysadmin@SERVER:~/`
- On server: `tar -xzf jarvis-framework.tar.gz && cp -r jarvis-framework/* jarvis/ && cp jarvis-framework/.gitignore jarvis/`

## Verification Checklist

- [ ] UFW active, only 22,80,443, tailscale0 allowed
- [ ] SSH: PermitRootLogin no, PasswordAuthentication no
- [ ] Fail2ban active
- [ ] .env 600 perms, not in git
- [ ] config.json from example, no secrets committed
- [ ] JWT_SECRET >=32 chars, random
- [ ] Device registry has only authorized devices, revocable
- [ ] API binds to 127.0.0.1, not 0.0.0.0 public, exposed via Tailscale
- [ ] Audit logs at logs/audit.jsonl, 600 perms
- [ ] Backup script tested
- [ ] Systemd service running as jarvis user, not root
- [ ] No secrets in git log: `git log -p | grep -i password` should be empty
- [ ] `python main.py status` shows online, security checks pass

## Rollback

```bash
cd ~/jarvis
git log --oneline -10
git revert <commit>
sudo systemctl restart jarvis
```

## Monitoring

- Background monitor: `python -m jarvis.core.background` (enable explicitly)
- Prometheus metrics via api (if enabled)
- Wazuh alerts via integration
- UFW logs: `sudo ufw logging on`
- Fail2ban: `sudo fail2ban-client status sshd`
