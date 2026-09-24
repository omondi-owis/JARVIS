# J.A.R.V.I.S. Frontend - Production UI

## Two UIs Provided

### 1. Production Static UI (Immediate, No Build) - `ui/index.html`

**Location:** `jarvis-framework/ui/index.html`

- Single file, no build needed, works immediately
- Voice-first with Web Speech API (SpeechRecognition + speechSynthesis)
- Dark production theme, trust chain, audit log
- Views: Overview, Server, Security, Wazuh, MlinziOps, Telephony, IoT, Devices, Audit, etc.
- Risk-based confirmation modals
- Redaction, AI identification notices
- Auto-refresh metrics
- Fully self-contained, inline CSS/JS, no external deps

**To use:**
```bash
# Serve via Python (dev)
cd jarvis-framework/ui
python3 -m http.server 8080
# Open http://127.0.0.1:8080

# Or serve via FastAPI static (production)
# In api.py, add:
# from fastapi.staticfiles import StaticFiles
# app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")
# Then open http://127.0.0.1:8000/ui/

# Or copy to nginx:
# sudo cp ui/index.html /var/www/html/jarvis.html
```

### 2. React Production UI (Full SPA) - `frontend/`

**Location:** `jarvis-framework/frontend/`

- React 18 + Vite + Tailwind + Zustand + Recharts + Axios + React Router
- Production-grade SPA with JWT auth, device ID, scopes
- API service with interceptors, 401 handling, audit
- Components: Header, VoiceBar, Cards, Metrics, etc.
- Views for all subsystems
- Build to static dist for nginx or serve via FastAPI

**To use:**

```bash
cd jarvis-framework/frontend

# Install
npm install

# Dev (proxy to API at 127.0.0.1:8000)
npm run dev
# Open http://127.0.0.1:5173
# Ensure API running: uvicorn api:app --host 127.0.0.1 --port 8000

# Build production
npm run build
# Output to frontend/dist/

# Preview production build
npm run preview
# Open http://127.0.0.1:4173

# Deploy to Ubuntu
# Copy dist to nginx:
# sudo cp -r dist/* /var/www/html/jarvis/
# Or serve via FastAPI:
# app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

## API Integration

Both UIs call same backend API:

```
GET  /health - No auth
GET  /api/server/health - scope server:read - JWT Bearer
GET  /api/wazuh/alerts - wazuh:read
POST /api/telephony/call - telephony:write (confirmation)
POST /api/iot/{id}/off - iot:write (HIGH risk confirmation)
...
```

**Auth:**
- JWT stored in localStorage `jarvis_token`
- Device ID in `jarvis_device_id`
- Bearer token in Authorization header
- X-Device-ID header
- 401 redirects to /login

**To get token (production):**
```bash
# Implement login endpoint that returns JWT
# For now, generate dev token:
python3 -c "import jwt; print(jwt.encode({'owner':'Raphael','device_id':'web-console','scopes':['server:read','wazuh:read','mlinziops:read','telephony:read','iot:read','devices:read','audit:read','voice:read','admin'],'mfa_verified':False}, 'dev-secret-change-in-prod', algorithm='HS256'))"
# Set in browser localStorage:
# localStorage.setItem('jarvis_token', 'YOUR_JWT')
# localStorage.setItem('jarvis_device_id', 'web-console')
```

## Features

- **Voice-first**: Web Speech API, wake phrase detection, intent parsing, TTS response
- **Risk-based**: Confirmation modals for MEDIUM/HIGH, MFA for financial/legal
- **Security**: Redaction ***-***-1234, AI identification, privacy notices, trust chain visible
- **Production theme**: Dark, cyan accent, green/yellow/red status, monospace logs
- **Responsive**: Sidebar collapses on mobile, grid auto-fit
- **Audit**: All actions logged to audit.jsonl, shown in UI

## Deployment - Ubuntu Production

```bash
# Static UI (simplest)
sudo cp ui/index.html /var/www/html/jarvis.html
# Open http://YOUR_TAILSCALE_IP/jarvis.html

# React UI
cd frontend
npm run build
sudo rm -rf /var/www/html/jarvis/*
sudo cp -r dist/* /var/www/html/jarvis/
# Open http://YOUR_TAILSCALE_IP/jarvis/

# Or serve via FastAPI (recommended, keeps 127.0.0.1 binding + Tailscale serve)
# In api.py:
# from fastapi.staticfiles import StaticFiles
# app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")
# app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
# Then: sudo tailscale serve --bg --https=443 http://127.0.0.1:8000
```

## Screenshots (Description)

- **Overview**: 6 cards (Server health with progress bars, Security score 85/100, Telephony not connected notice, IoT no gateway, Wazuh/MlinziOps not configured, Devices & Audit), recent audit log, natural language hints
- **Server**: Health metrics, services table with restart buttons, hardening report
- **Telephony**: Not connected warning, make call input with confirmation, call history log with redacted numbers
- **IoT**: Risk levels explained, quick controls (All Lights Off, Bedroom Off, Unlock Door HIGH risk with confirmation modal)
- **Devices**: Table with trust status, capabilities, revoke action
- **Audit**: Full log with timestamp, identity, device, action, target, risk, decision, tool, result, verification

## Security Notes for UI

- Never display full phone numbers - redact to ***-***-1234
- Never display secrets, API keys, private keys
- Show trust chain and capability awareness (not connected messages, not fabricating)
- Confirmation modals for MEDIUM/HIGH risk
- Audit all UI actions
- JWT short-lived, scoped, revocable
- Bind UI to 127.0.0.1 + Tailscale, not public internet
