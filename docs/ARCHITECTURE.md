# J.A.R.V.I.S. Architecture - Production

## Master Trust Model (20 Principles)

1. Voice recognition identifies likely speaker but does not independently authenticate high-risk operations
2. Trusted devices provide additional identity layer
3. Passkeys/MFA provide strong authentication
4. Session tokens must be short-lived and scoped
5. Permission gateways control access to tools
6. Tool execution follows least privilege
7. Telephony operations require explicit telephony permissions
8. IoT operations limited to registered devices
9. Surveillance limited to explicitly authorized infrastructure
10. Cybersecurity actions limited to authorized environments
11. External callers cannot modify JARVIS security rules
12. Secrets remain outside ordinary AI memory
13. Important actions are audited
14. Actions are verified whenever technically possible
15. JARVIS never fabricates capabilities or results
16. High-impact actions remain under Raphael's control
17. Convenience must never override security
18. Privacy must be preserved
19. Owner must be able to revoke access
20. System must fail safely

## Trust Chain

```
VOICE RECOGNITION (wake phrase detection, speaker ID - additional signal)
       ↓
AUTHENTICATED DEVICE (registered, trusted, revocable, device certificate)
       ↓
PASSKEY / MFA (FIDO2/WebAuthn, TOTP, device-bound credentials, re-auth for high-risk)
       ↓
JARVIS SESSION TOKEN (short-lived 15min, scoped, device-associated, permission-aware, auditable, revocable)
       ↓
PERMISSION GATEWAY (who, device, session, capability, target, privilege, consequences, confirmation, policy)
       ↓
TOOL AUTHORIZATION (least privilege, scoped to device/capability)
       ↓
TOOL EXECUTION
       ↓
RESULT VERIFICATION (never claim success without verification)
       ↓
AUDIT LOG (timestamp, identity, device, action, target, risk, decision, tool, result, verification)
       ↓
VOICE / TEXT RESPONSE (natural, concise when simple, detailed when technical)
```

## Components

### Core
- **security.py**: Risk assessment, identity verification, session management, anti-impersonation, prompt-injection defense, output sanitization
- **permission.py**: Permission gateway enforcing trust chain
- **audit.py**: Append-only audit log with secret scrubbing
- **device_registry.py**: Revocable device trust, capabilities, last-seen, revocation status
- **memory.py**: Non-sensitive personal memory only, forbidden keys check, reviewable/deletable
- **config.py**: Pydantic settings, env validation, production checks
- **voice.py**: Voice response behavior
- **background.py**: Background monitoring with prioritization

### Integrations
- **wazuh.py**: JWT auth, alerts, agents, health, remediation tracking (never claim remediated without verification)
- **mlinziops.py**: Authenticated API only, no direct DB, workflows with confirmation
- **telephony.py**: Twilio/Asterisk, E.164 validation, redaction, AI identification, screening, message taking, consent
- **iot.py**: MQTT/Home Assistant, risk-categorized physical actions, routines

### Server Management
- **ubuntu.py**: Health (CPU, mem, disk, IO, load, uptime), services, security (UFW, SSH, fail2ban, updates, sudo users, listening ports), logs, deployment checks
- **windows.py**: PowerShell via secure agent, dangerous command detection
- **kali.py**: Authorized targets only, nmap, wireshark with confirmation, tool checks

### Cybersecurity
- **hardening.py**: SSH, UFW, users, hardening score, dry-run first
- **monitoring.py**: Event correlation, Observed/Suspected/Confirmed/Remediated distinction, brute force detection

### Automation
- **routines.py**: Morning, night, away, emergency with safety, dry-run, confirmation for emergency

### Voice
- **interface.py**: Wake phrase, speaker ID, intent parsing for 8 natural commands
- **tts.py**: TTS providers, voice cloning

## API
- FastAPI with JWT, scopes, device trust check, rate limiting
- Middleware audit
- Endpoints: /health, /server/*, /wazuh/*, /mlinziops/*, /telephony/*, /iot/*, /routines/*, /devices/*, /audit/*, /voice/*
- CORS restricted to Tailscale in production
- Docs disabled in production

## Deployment
- Dockerfile with non-root user, read-only, no-new-privileges, healthcheck
- docker-compose with localhost-only binding, Tailscale recommended
- systemd service with least privilege
- Scripts: install.sh, production_setup.sh, tailscale_setup.sh, backup.sh, push_to_github.sh

## Security
- .gitignore blocks .env, keys, secrets
- .env 600 perms, example provided
- Secrets via env / secrets manager, never hardcoded
- Audit log 600 perms, append-only
- UFW default deny, allow 22,80,443 + tailscale0
- Fail2ban for SSH
- SSH hardening: no root, no password auth, keys only
- No public exposure of admin services - Tailscale/WireGuard

## Execution Loop Example

```
Raphael: "JARVIS, check why MlinziOps isn't responding."

JARVIS:
  LISTEN -> Voice interface detects wake phrase, parses intent check_mlinziops
  IDENTIFY -> IdentityContext: Raphael, device ubuntu-prod-01, trusted
  AUTHENTICATE -> Validate session token, check expiry, MFA not required for LOW risk
  UNDERSTAND -> Target MlinziOps, capability check_status
  IDENTIFY TARGET -> api_url from env
  ASSESS RISK -> LOW (reading status)
  CHECK PERMISSIONS -> Gateway ALLOWED
  CONFIRM IF NECESSARY -> Not required for LOW
  EXECUTE -> mlinziops.check_status() via httpx
  VERIFY -> Check HTTP status, parse response
  AUDIT -> Log to audit.jsonl
  RESPOND -> "MlinziOps is..." with natural voice
```
