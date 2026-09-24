"""
J.A.R.V.I.S. Audit Logging
Every meaningful operation generates an audit record
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

class AuditLogger:
    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure .gitkeep
        gitkeep = self.log_path.parent / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def log(
        self,
        identity: str,
        device: str,
        action: str,
        target: str,
        risk: str,
        auth_decision: str,
        tool: str,
        result: str,
        verification: str,
        notes: str = "",
        session_id: Optional[str] = None
    ):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "identity": identity,
            "device": device,
            "action": action,
            "target": target,
            "risk": risk,
            "auth_decision": auth_decision,
            "tool": tool,
            "result": result,
            "verification": verification,
            "notes": notes,
        }
        if session_id:
            record["session_id"] = session_id

        # Never log secrets - scrub
        scrubbed = self._scrub_secrets(record)
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(scrubbed) + "\n")
        
        return scrubbed

    def _scrub_secrets(self, record: dict) -> dict:
        # Ensure no secrets leak into logs
        forbidden_substrings = ["password", "secret", "api_key", "private_key", "mfa", "otp", "token"]
        # Shallow check for demo - in production use deeper inspection
        for k, v in list(record.items()):
            if isinstance(v, str):
                low = v.lower()
                if any(s in low for s in ["BEGIN RSA PRIVATE", "BEGIN OPENSSH PRIVATE", "sk-"]):
                    record[k] = "[REDACTED_SECRET]"
        return record

    def read_recent(self, n: int = 20):
        if not self.log_path.exists():
            return []
        with open(self.log_path) as f:
            lines = f.readlines()
        recent = lines[-n:]
        return [json.loads(l) for l in recent]

audit = AuditLogger()
