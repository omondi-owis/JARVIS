# J.A.R.V.I.S. — Private Remote Voice AI & Operations System
## PRODUCTION LEVEL - FULL FRAMEWORK

**Owner:** Raphael  
**Version:** Advanced Personal Assistant v1.0 Production  
**Security:** Master Trust Model 20 principles, least privilege, auditable, verified

---

## 🚀 Production Features - Complete

### Core Security (Production-Grade)
- ✅ Trust chain: Voice → Device → Passkey/MFA → Session Token → Permission Gateway → Tool → Verify → Audit → Response
- ✅ Risk-based execution: LOW/MEDIUM/HIGH with MFA & confirmation
- ✅ Session management: Short-lived JWT (15min), scoped, revocable, device-bound
- ✅ Anti-impersonation & prompt-injection defense
- ✅ Audit logging with secret scrubbing, 600 perms, append-only
- ✅ Device registry: Revocable, capabilities, last-seen, trust status
- ✅ Personal memory: Non-sensitive only, forbidden keys check, reviewable/deletable
- ✅ Config management: Pydantic, env validation, production checks

### Integrations (Full Implementation)
- ✅ **Wazuh**: JWT auth, alerts, agents, health, manager status, remediation tracking (never claim remediated without verification)
- ✅ **MlinziOps**: Authenticated API, health, alerts, deployments, workflows with confirmation, no direct DB
- ✅ **Telephony**: Twilio/Asterisk, E.164 validation, redaction, AI identification, screening, message taking, consent, call history
- ✅ **IoT**: MQTT/Home Assistant, risk-categorized physical actions (LOW lights, MEDIUM thermostat, HIGH locks), routines, temperature control

### Server Management (Production)
- ✅ **Ubuntu**: Health (CPU, mem, disk, IO, load, uptime, users), services, security (UFW, SSH hardening, fail2ban, updates, sudo users, listening ports), logs, deployment checks
- ✅ **Windows**: Secure agent, PowerShell with dangerous command detection
- ✅ **Kali Lab**: Authorized targets only, nmap, wireshark, tool checks, audit

### Cybersecurity Operations
- ✅ Hardening: SSH, UFW, users, score, dry-run first, confirmation for HIGH risk
- ✅ Monitoring: Event correlation, Observed/Suspected/Confirmed/Remediated, brute force detection

### Automation & Voice
- ✅ Routines: Morning, night, away, emergency with safety, dry-run, confirmation
- ✅ Voice interface: Wake phrase, speaker ID, intent parsing for 8 natural commands
- ✅ TTS: Multi-provider, voice cloning ready

### API & Deployment
- ✅ FastAPI with JWT, scopes, device trust, rate limiting, audit middleware, CORS restricted to Tailscale in prod
- ✅ Dockerfile: Non-root jarvis user, read-only, no-new-privileges, healthcheck
- ✅ docker-compose: Localhost-only binding, Tailscale recommended, Redis, security opts
- ✅ systemd: Least privilege service
- ✅ Scripts: install.sh, production_setup.sh, tailscale_setup.sh, backup.sh, push_to_github.sh
- ✅ CI/CD: GitHub Actions with secret checks, tests, hardening checks, deploy via Tailscale
- ✅ Tests: Security, device registry
- ✅ Docs: Architecture, Security, Deployment

---

## 📦 Folder Structure - Production

```
jarvis/
├── .github/workflows/
│   ├── ci.yml                    # Secret checks, tests, hardening
│   └── deploy.yml                # Deploy via Tailscale with verification
├── config/
│   ├── config.example.json       # Production config example
│   ├── device_registry.example.json
│   ├── iot_devices.example.json  # IoT devices with risk levels
│   └── tailscale/                # Tailscale configs
├── docker/
│   └── (Dockerfile, compose)
├── docs/
│   ├── ARCHITECTURE.md           # Trust chain, components, execution loop
│   ├── SECURITY.md               # Credential security, auth, risk, privacy
│   └── DEPLOYMENT.md             # Ubuntu prod setup, Tailscale, verification
├── jarvis/
│   ├── core/
│   │   ├── security.py           # Production session, MFA, rate limit, injection defense
│   │   ├── permission.py         # Gateway
│   │   ├── audit.py              # Scrubbing, append-only
│   │   ├── device_registry.py    # Revocable
│   │   ├── memory.py             # Non-sensitive only
│   │   ├── config.py             # Pydantic, validation
│   │   ├── voice.py              # Voice response behavior
│   │   └── background.py         # Monitoring with prioritization
│   ├── integrations/
│   │   ├── wazuh.py              # Full JWT, alerts, agents
│   │   ├── mlinziops.py          # Full API client
│   │   ├── telephony.py          # Full Twilio, screening, redaction
│   │   └── iot.py                # Full MQTT, risk, routines
│   ├── server/
│   │   ├── ubuntu.py             # Full health, services, security, logs, deploy
│   │   ├── windows.py            # PowerShell via agent
│   │   └── kali.py               # Authorized targets only
│   ├── cybersecurity/
│   │   ├── hardening.py          # CIS, SSH, UFW, score
│   │   └── monitoring.py         # Correlation, Observed/Suspected/Confirmed/Remediated
│   ├── automation/
│   │   └── routines.py           # Morning, night, away, emergency
│   └── voice/
│       ├── interface.py          # Wake phrase, intent parsing
│       └── tts.py                # TTS providers
├── scripts/
│   ├── install.sh                # Dev install
│   ├── production_setup.sh       # Prod hardening, UFW, fail2ban, venv, config
│   ├── tailscale_setup.sh        # Secure remote access
│   ├── backup.sh                 # Backup config, logs, memory (no secrets plain)
│   └── push_to_github.sh         # Safe push with secret check
├── systemd/
│   └── jarvis.service            # Least privilege
├── tests/
│   ├── test_security.py
│   └── test_device_registry.py
├── logs/
│   └── .gitkeep
├── main.py                       # Production CLI with 12 commands
├── api.py                        # Production FastAPI with JWT, scopes, audit
├── requirements.txt              # Core
├── requirements-prod.txt         # Prod extras (gunicorn, redis, twilio, mqtt, webauthn)
├── .env.example                  # All env vars
├── .gitignore                    # Blocks .env, keys, secrets
├── Dockerfile                    # Non-root, read-only, healthcheck
├── docker-compose.yml            # Localhost-only, Tailscale, Redis
└── README.md                     # This file
```

---

## 🔐 Quick Start - Production on Ubuntu

### 1. Clone (as sysadmin, not root)

```bash
ssh sysadmin@YOUR_SERVER
cd ~
git clone git@github.com:omondi-owis/JARVIS.git jarvis
cd jarvis
ls -la
```

### 2. Production Setup

```bash
chmod +x scripts/production_setup.sh
./scripts/production_setup.sh
# - Updates system
# - Installs Python 3.11, UFW, fail2ban
# - Configures UFW: deny incoming, allow 22,80,443, tailscale0
# - Enables fail2ban
# - Creates jarvis user
# - Venv + prod requirements
# - Config from examples, .env 600 perms
```

### 3. Configure Secrets (600 perms, never commit)

```bash
nano .env
# Generate JWT:
# openssl rand -base64 32

# Set:
# JWT_SECRET=your_32+_chars_random
# WAZUH_API_URL=https://YOUR_WAZUH:55000
# WAZUH_API_USER=...
# WAZUH_API_PASS=...
# MLINZIOPS_API_URL=...
# MLINZIOPS_API_KEY=...
# TWILIO_ACCOUNT_SID=...
# TWILIO_AUTH_TOKEN=...
# TWILIO_PHONE_NUMBER=...
# MQTT_BROKER=...
# TAILSCALE_AUTHKEY=tskey-auth-...

chmod 600 .env
```

### 4. Device Registry

```bash
nano config/device_registry.json
# Register: ubuntu-prod-01, sec-lab-kali, windows, etc.
# trust_status: trusted, revocation_status: active

nano config/config.json
# Enable integrations
```

### 5. Tailscale (Highly Recommended - No Public Exposure)

```bash
export TAILSCALE_AUTHKEY=tskey-auth-xxxx
sudo -E ./scripts/tailscale_setup.sh
# Or:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY --ssh --advertise-tags=tag:jarvis
sudo tailscale serve --bg --https=443 http://127.0.0.1:8000
```

### 6. Test

```bash
source .venv/bin/activate
python main.py status
python main.py hardening-report
python main.py devices
python main.py security-events
python main.py voice-parse "JARVIS, check the server"

# API
uvicorn api:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health
```

### 7. Systemd

```bash
sudo cp systemd/jarvis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis
sudo systemctl status jarvis
sudo journalctl -u jarvis -f
```

### 8. Docker Alternative

```bash
docker-compose up -d --build
docker-compose logs -f jarvis
# API at 127.0.0.1:8000, expose via Tailscale, not public
```

---

## 📤 Push to GitHub - From Ubuntu Server

**After you download this production framework:**

```bash
cd ~/jarvis

# Check remote
git remote -v
# origin git@github.com:omondi-owis/JARVIS.git

# Copy production files (from downloaded jarvis-framework.tar.gz)
# scp jarvis-framework.tar.gz sysadmin@SERVER:~/
# tar -xzf ~/jarvis-framework.tar.gz
# cp -r ~/jarvis-framework/jarvis-framework/* ~/jarvis/
# cp ~/jarvis-framework/jarvis-framework/.gitignore ~/jarvis/
# cp ~/jarvis-framework/jarvis-framework/.env.example ~/jarvis/  (not .env!)
# Ensure hidden files copied

# Safety check - MUST NOT show secrets
git status
# Should NOT show: .env, *.key, *.pem, id_ed25519, config/config.json
# If it does, check .gitignore

# Stage
git add .

# Commit
git commit -m "feat: production JARVIS - full security, Wazuh/MlinziOps full, telephony, IoT, hardening, Tailscale, API JWT, CI/CD

- Master Trust Model 20 principles production-grade
- Session JWT short-lived scoped revocable, MFA, rate limit
- Wazuh full client JWT auth alerts agents
- MlinziOps full API workflows
- Telephony Twilio E.164 redaction AI identification screening
- IoT MQTT risk-categorized routines
- Ubuntu full health services security logs deploy checks
- Windows/Kali agents authorized targets only
- Hardening CIS score, monitoring correlation Observed/Suspected/Confirmed/Remediated
- Automation morning/night/away/emergency
- Voice interface intent parsing 8 commands
- FastAPI JWT scopes device trust audit middleware
- Dockerfile non-root read-only healthcheck
- docker-compose localhost-only Tailscale Redis
- Production scripts UFW fail2ban backup
- Docs architecture security deployment
- CI/CD secret checks tests hardening"

git branch -M main
git push -u origin main

git log --oneline -5
```

**Verify on GitHub:** https://github.com/omondi-owis/JARVIS
- No secrets, .env not present
- All production files present
- README shows production

---

## 🗣️ Natural Language Commands - Production

```bash
python main.py status                                    # "JARVIS, check the server."
python main.py wazuh-alerts --limit 20                   # "JARVIS, what's happening with Wazuh?"
python main.py call 0712345678 --contact Brian --purpose routine  # "JARVIS, call Brian."
python main.py lights --action off --room bedroom        # "JARVIS, turn off the bedroom lights."
python main.py routine night                             # "JARVIS, run night routine"
python main.py routine morning --dry-run                 # Dry run first
python main.py devices                                   # List authorized devices
python main.py hardening-report                          # "JARVIS, make sure my Ubuntu server is secure."
python main.py security-events --hours 24                # Security correlations
python main.py voice-parse "JARVIS, check the cameras"   # Intent parsing
python main.py memory-review                             # Review non-sensitive memory
python main.py check-service nginx                       # Check service
python main.py restart-service nginx                     # Requires confirmation (MEDIUM risk)
```

---

## 🔒 Security Checklist - Production

- [ ] UFW active, only 22,80,443, tailscale0 allowed: `sudo ufw status verbose`
- [ ] SSH: PermitRootLogin no, PasswordAuthentication no, Port 22 or non-standard, keys only
- [ ] Fail2ban active: `sudo fail2ban-client status sshd`
- [ ] .env 600 perms, not in git: `ls -l .env` should show `-rw-------`, `git status` should NOT show .env
- [ ] config.json from example, no secrets committed
- [ ] JWT_SECRET >=32 chars random: `openssl rand -base64 32`
- [ ] Device registry only authorized devices, revocable: `python main.py devices`
- [ ] API binds to 127.0.0.1, not 0.0.0.0 public, exposed via Tailscale serve
- [ ] Audit logs at logs/audit.jsonl, 600 perms, append-only
- [ ] Backup script tested: `./scripts/backup.sh`, backups in /home/sysadmin/backups/jarvis/
- [ ] Systemd service running as jarvis user, not root: `systemctl status jarvis`
- [ ] No secrets in git log: `git log -p | grep -i password` should be empty
- [ ] `python main.py status` shows online, security checks pass, hardening score >80
- [ ] Tailscale up and serving: `tailscale status`, `tailscale ip -4`
- [ ] Docker read-only, no-new-privileges, healthcheck

---

## 📥 Download & Push - YES, You Can

**YES, you can download this production framework and push to GitHub.**

**Files in this workspace:**
- `jarvis-framework/` folder with 50+ production files
- `jarvis-framework.tar.gz` (16KB+) - download this

**To download:**
1. In Arena workspace, find `jarvis-framework.tar.gz`
2. Download it (browser download)
3. SCP to Ubuntu: `scp jarvis-framework.tar.gz sysadmin@YOUR_SERVER:~/`
4. On Ubuntu:
```bash
tar -xzf ~/jarvis-framework.tar.gz
cp -r ~/jarvis-framework/jarvis-framework/* ~/jarvis/
cp ~/jarvis-framework/jarvis-framework/.gitignore ~/jarvis/
cp ~/jarvis-framework/jarvis-framework/.env.example ~/jarvis/
# Don't overwrite .env if you have secrets!
```

**Then push:**
```bash
cd ~/jarvis
chmod +x scripts/*.sh
./scripts/push_to_github.sh
# Or manual: git add . && git commit -m "feat: production" && git push -u origin main
```

**After push, verify:**
- GitHub repo has all files, no secrets
- Actions CI passes (secret checks, tests, hardening)
- On Ubuntu, run production_setup.sh and test

---

## 📚 Docs

- `docs/ARCHITECTURE.md` - Trust chain, components, execution loop example
- `docs/SECURITY.md` - Credential security, auth, risk, privacy, audit, network, backup
- `docs/DEPLOYMENT.md` - Ubuntu prod setup, Tailscale, verification, rollback, monitoring

---

## ⚠️ Never Claim Success Without Verification

Every operation:
1. LISTEN
2. IDENTIFY
3. AUTHENTICATE
4. UNDERSTAND
5. IDENTIFY TARGET
6. ASSESS RISK
7. CHECK PERMISSIONS
8. CONFIRM IF NECESSARY
9. EXECUTE
10. VERIFY
11. AUDIT
12. RESPOND

Example: Deployment not successful until service verified active.

---

**You are J.A.R.V.I.S. — Raphael's private system.**

**Security, privacy, verification, and owner control are fundamental.**

**Never sacrifice authentication for convenience.**

**Never sacrifice privacy for capability.**

**Never sacrifice safety for autonomy.**

**Never claim success without verification.**
