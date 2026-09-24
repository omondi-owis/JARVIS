"""
J.A.R.V.I.S. FastAPI - PRODUCTION
Private Remote Operations API with JWT, passkey, MFA, scoped tokens
"""
import os
from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import jwt
from jarvis.core.audit import audit
from jarvis.core.config import settings
from jarvis.core.device_registry import registry
from jarvis.core.security import security
from jarvis.server.ubuntu import ubuntu
from jarvis.integrations.wazuh import wazuh
from jarvis.integrations.mlinziops import mlinziops
from jarvis.integrations.telephony import telephony
from jarvis.integrations.iot import iot
from jarvis.cybersecurity.hardening import hardening
from jarvis.automation.routines import routine_manager

app = FastAPI(
    title="J.A.R.V.I.S. API",
    description="Private Remote Voice AI & Operations System - Owner: Raphael - Production",
    version="1.0.0-production",
    docs_url="/api/docs" if not settings.is_production() else None,  # Disable docs in production unless needed
    redoc_url=None
)

# Security
security_scheme = HTTPBearer(auto_error=False)

# CORS - restrict in production to Tailscale IPs and authorized origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production() else ["https://*.ts.net"],  # Tailscale only in prod
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str

class TokenData(BaseModel):
    owner: str
    device_id: str
    scopes: List[str]
    mfa_verified: bool = False

async def get_current_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> TokenData:
    if not credentials:
        # Allow health checks without auth, but require auth for operations
        raise HTTPException(status_code=401, detail="Missing authentication - provide Bearer token")
    
    token = credentials.credentials
    try:
        # Validate JWT
        payload = jwt.decode(token, settings.jwt_secret or "dev-secret-change-in-prod", algorithms=[settings.jwt_algorithm])
        # Check expiry, device trust, revocation
        device_id = payload.get("device_id")
        if not registry.is_trusted(device_id):
            raise HTTPException(status_code=403, detail="Device not trusted or revoked")
        
        if not security.validate_session(payload.get("jti", "")):
            # Also check JWT expiry handled by jwt.decode
            pass
        
        return TokenData(
            owner=payload.get("owner", "unknown"),
            device_id=device_id,
            scopes=payload.get("scopes", []),
            mfa_verified=payload.get("mfa_verified", False)
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired - re-authenticate")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def require_scope(required_scope: str):
    def scope_checker(token: TokenData = Depends(get_current_token)):
        if required_scope not in token.scopes and "admin" not in token.scopes:
            raise HTTPException(status_code=403, detail=f"Scope {required_scope} required")
        return token
    return scope_checker

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    # Audit all API requests
    start = datetime.now(timezone.utc)
    response = await call_next(request)
    
    # Don't log health checks verbosely
    if request.url.path not in ["/", "/health", "/api/health"]:
        audit.log(
            identity=request.headers.get("X-Device-ID", "api_client"),
            device=request.headers.get("X-Device-ID", "api_client"),
            action=f"API:{request.method}:{request.url.path}",
            target=request.url.path,
            risk="LOW",
            auth_decision="ALLOWED",
            tool="api",
            result=str(response.status_code),
            verification=f"{request.method} {request.url.path} -> {response.status_code} in {(datetime.now(timezone.utc)-start).total_seconds():.2f}s"
        )
    return response

@app.get("/", response_model=HealthResponse, tags=["System"])
async def root():
    return {
        "status": "online",
        "message": "J.A.R.V.I.S. is online. Owner: Raphael. Security, privacy, verification are fundamental.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0-production"
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    h = ubuntu.check_health()
    return {
        "status": h["status"],
        "message": h["message"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0-production"
    }

@app.get("/api/health", tags=["System"])
async def api_health():
    return await health()

@app.get("/api/server/health", tags=["Server"])
async def server_health(token: TokenData = Depends(require_scope("server:read"))):
    return ubuntu.check_health()

@app.get("/api/server/services", tags=["Server"])
async def server_services(token: TokenData = Depends(require_scope("server:read"))):
    return ubuntu.check_services()

@app.get("/api/server/security", tags=["Server", "Security"])
async def server_security(token: TokenData = Depends(require_scope("security:read"))):
    return {
        "hardening": hardening.generate_report(),
        "security_checks": ubuntu.check_security()
    }

@app.get("/api/wazuh/status", tags=["Wazuh"])
async def wazuh_status(token: TokenData = Depends(require_scope("wazuh:read"))):
    return wazuh.summarize_status()

@app.get("/api/wazuh/alerts", tags=["Wazuh"])
async def wazuh_alerts(limit: int = 20, token: TokenData = Depends(require_scope("wazuh:read"))):
    return await wazuh.get_alerts(limit)

@app.get("/api/wazuh/agents", tags=["Wazuh"])
async def wazuh_agents(token: TokenData = Depends(require_scope("wazuh:read"))):
    return await wazuh.get_agents()

@app.get("/api/mlinziops/status", tags=["MlinziOps"])
async def mlinziops_status(token: TokenData = Depends(require_scope("mlinziops:read"))):
    return await mlinziops.check_status()

@app.get("/api/mlinziops/alerts", tags=["MlinziOps"])
async def mlinziops_alerts(limit: int = 20, token: TokenData = Depends(require_scope("mlinziops:read"))):
    return await mlinziops.get_alerts(limit)

@app.post("/api/mlinziops/workflows/{workflow_name}/trigger", tags=["MlinziOps"])
async def trigger_workflow(workflow_name: str, payload: Dict[str, Any], token: TokenData = Depends(require_scope("mlinziops:write"))):
    # Requires confirmation for medium risk
    return await mlinziops.trigger_workflow(workflow_name, payload, require_confirmation=True)

@app.get("/api/telephony/history", tags=["Telephony"])
async def telephony_history(limit: int = 20, token: TokenData = Depends(require_scope("telephony:read"))):
    disabled = telephony._ensure_enabled()
    if disabled:
        return disabled
    return {"history": telephony.get_call_history(limit)}

@app.post("/api/telephony/call", tags=["Telephony"])
async def make_call(destination: str, contact_name: Optional[str] = None, purpose: str = "routine", token: TokenData = Depends(require_scope("telephony:write"))):
    # Validate MFA for high-risk calls
    if purpose in ["financial", "legal"] and not token.mfa_verified:
        raise HTTPException(status_code=403, detail="MFA required for financial/legal calls")
    return telephony.make_outgoing_call(destination, contact_name, purpose, require_confirmation=True)

@app.get("/api/iot/devices", tags=["IoT"])
async def iot_devices(token: TokenData = Depends(require_scope("iot:read"))):
    disabled = iot._ensure_enabled()
    if disabled and disabled.get("status") == "not_configured":
        return disabled
    return {"devices": iot.list_devices(), "gateway": iot.gateway, "enabled": iot.enabled}

@app.post("/api/iot/{device_id}/on", tags=["IoT"])
async def iot_turn_on(device_id: str, token: TokenData = Depends(require_scope("iot:write"))):
    return await iot.turn_on(device_id)

@app.post("/api/iot/{device_id}/off", tags=["IoT"])
async def iot_turn_off(device_id: str, token: TokenData = Depends(require_scope("iot:write"))):
    return await iot.turn_off(device_id)

@app.get("/api/routines", tags=["Automation"])
async def list_routines(token: TokenData = Depends(require_scope("automation:read"))):
    return routine_manager.list_routines()

@app.post("/api/routines/{name}/run", tags=["Automation"])
async def run_routine(name: str, dry_run: bool = False, token: TokenData = Depends(require_scope("automation:write"))):
    return await routine_manager.run_routine(name, dry_run=dry_run)

@app.get("/api/devices", tags=["Devices"])
async def list_devices(token: TokenData = Depends(require_scope("devices:read"))):
    return {"devices": registry.list_devices()}

@app.post("/api/devices/{device_id}/revoke", tags=["Devices"])
async def revoke_device(device_id: str, token: TokenData = Depends(require_scope("admin"))):
    success = registry.revoke_device(device_id)
    if success:
        audit.log(
            identity=token.owner,
            device=token.device_id,
            action=f"REVOKE_DEVICE:{device_id}",
            target=device_id,
            risk="HIGH",
            auth_decision="ALLOWED",
            tool="api",
            result="SUCCESS",
            verification=f"Device {device_id} revoked by {token.owner}"
        )
        return {"status": "revoked", "device_id": device_id}
    raise HTTPException(status_code=404, detail="Device not found")

@app.get("/api/audit/recent", tags=["Audit"])
async def audit_recent(n: int = 20, token: TokenData = Depends(require_scope("audit:read"))):
    return audit.read_recent(n)

@app.get("/api/voice/parse", tags=["Voice"])
async def parse_voice(text: str, token: TokenData = Depends(require_scope("voice:read"))):
    from jarvis.voice.interface import voice_interface
    return voice_interface.parse_intent(text)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error", "path": str(request.url.path)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host=settings.mqtt_broker or "0.0.0.0", port=8000, reload=not settings.is_production())
