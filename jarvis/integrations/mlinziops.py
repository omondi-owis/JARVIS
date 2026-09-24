"""
MlinziOps Integration - PRODUCTION
Intelligent interface to MlinziOps via authenticated APIs
Never bypass application security by direct DB modification unless explicitly authorized via secure admin mechanism
"""
import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ..core.audit import audit
from ..core.config import settings

class MlinziOpsClient:
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or settings.mlinziops_api_url or os.getenv("MLINZIOPS_API_URL")
        self.api_key = api_key or settings.mlinziops_api_key or os.getenv("MLINZIOPS_API_KEY")
        self.enabled = bool(self.api_url and self.api_key)
        self.client = httpx.AsyncClient(timeout=30, headers=self._headers())

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        return headers

    def _check_enabled(self):
        if not self.enabled:
            return {
                "status": "not_configured",
                "message": "The MlinziOps integration is not currently connected, so I cannot check application status.",
                "required_env": ["MLINZIOPS_API_URL", "MLINZIOPS_API_KEY"]
            }
        return None

    async def check_status(self) -> Dict[str, Any]:
        disabled = self._check_enabled()
        if disabled:
            return disabled
        
        try:
            # Health check endpoints - adapt to actual MlinziOps API
            endpoints_to_try = ["/health", "/api/health", "/status", "/api/v1/health"]
            last_error = None
            
            for ep in endpoints_to_try:
                try:
                    url = f"{self.api_url.rstrip('/')}{ep}"
                    resp = await self.client.get(url)
                    if resp.status_code < 500:
                        result = {
                            "status": "online" if resp.status_code == 200 else f"http_{resp.status_code}",
                            "api_url": self.api_url,
                            "endpoint": ep,
                            "code": resp.status_code,
                            "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:500]
                        }
                        audit.log(
                            identity="JARVIS",
                            device="mlinziops",
                            action="MLINZIOPS_CHECK_STATUS",
                            target=self.api_url,
                            risk="LOW",
                            auth_decision="ALLOWED",
                            tool="mlinziops_api",
                            result="SUCCESS",
                            verification=f"Health check {ep}: {resp.status_code}"
                        )
                        return result
                except Exception as e:
                    last_error = str(e)
                    continue
            
            return {
                "status": "unreachable",
                "api_url": self.api_url,
                "error": last_error,
                "tried_endpoints": endpoints_to_try
            }

        except Exception as e:
            audit.log(
                identity="JARVIS",
                device="mlinziops",
                action="MLINZIOPS_CHECK_STATUS",
                target=self.api_url,
                risk="LOW",
                auth_decision="ALLOWED",
                tool="mlinziops_api",
                result="FAILED",
                verification=f"Exception: {str(e)}"
            )
            return {"status": "failed", "error": str(e), "api_url": self.api_url}

    async def get_alerts(self, limit: int = 20) -> Dict[str, Any]:
        disabled = self._check_enabled()
        if disabled:
            return disabled
        
        try:
            url = f"{self.api_url.rstrip('/')}/api/v1/alerts?limit={limit}"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return {"status": "success", "alerts": resp.json()}
            else:
                return {"status": f"http_{resp.status_code}", "error": resp.text[:500]}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def get_deployments(self) -> Dict[str, Any]:
        disabled = self._check_enabled()
        if disabled:
            return disabled
        
        try:
            url = f"{self.api_url.rstrip('/')}/api/v1/deployments"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return {"status": "success", "deployments": resp.json()}
            else:
                # Try alternative
                url2 = f"{self.api_url.rstrip('/')}/deployments"
                resp2 = await self.client.get(url2)
                if resp2.status_code == 200:
                    return {"status": "success", "deployments": resp2.json()}
                return {"status": f"http_{resp.status_code}", "error": resp.text[:300]}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def trigger_workflow(self, workflow_name: str, payload: Dict[str, Any], require_confirmation: bool = True) -> Dict[str, Any]:
        disabled = self._check_enabled()
        if disabled:
            return disabled
        
        if require_confirmation:
            audit.log(
                identity="Raphael",
                device="mlinziops",
                action=f"MLINZIOPS_WORKFLOW:{workflow_name}",
                target=self.api_url,
                risk="MEDIUM",
                auth_decision="REQUIRES_CONFIRMATION",
                tool="mlinziops_api",
                result="PENDING_CONFIRMATION",
                verification=f"Workflow {workflow_name} requires explicit authorization",
                notes=str(payload)[:300]
            )
            return {
                "status": "requires_confirmation",
                "message": f"This will trigger MlinziOps workflow '{workflow_name}'. Proceed?",
                "workflow": workflow_name,
                "payload_preview": str(payload)[:200]
            }
        
        try:
            url = f"{self.api_url.rstrip('/')}/api/v1/workflows/{workflow_name}/trigger"
            resp = await self.client.post(url, json=payload)
            
            audit.log(
                identity="Raphael",
                device="mlinziops",
                action=f"MLINZIOPS_WORKFLOW:{workflow_name}",
                target=self.api_url,
                risk="MEDIUM",
                auth_decision="ALLOWED",
                tool="mlinziops_api",
                result="SUCCESS" if resp.status_code in [200, 201, 202] else "FAILED",
                verification=f"Workflow trigger: {resp.status_code}"
            )
            
            return {
                "status": "triggered" if resp.status_code in [200, 201, 202] else f"http_{resp.status_code}",
                "workflow": workflow_name,
                "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:500]
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def create_record(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # Only via authenticated API, never direct DB
        disabled = self._check_enabled()
        if disabled:
            return disabled
        
        try:
            url = f"{self.api_url.rstrip('/')}/api/v1/{collection}"
            resp = await self.client.post(url, json=data)
            return {"status": "created" if resp.status_code in [200, 201] else f"http_{resp.status_code}", "response": resp.text[:500]}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def close(self):
        await self.client.aclose()

mlinziops = MlinziOpsClient()
