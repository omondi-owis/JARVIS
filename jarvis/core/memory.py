"""
J.A.R.V.I.S. Personal Memory - Non-sensitive only
Owner can review, correct, delete, restrict categories, disable
Never store passwords, private keys, API keys, MFA secrets, etc.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from .audit import audit

FORBIDDEN_MEMORY_KEYS = {
    "password", "private_key", "api_key", "mfa_secret", "recovery_code",
    "session_token", "banking", "credit_card", "ssn", "secret", "token",
    "otp", "passphrase", "secret_key"
}

class PersonalMemory:
    def __init__(self, memory_path: str = "config/memory.json"):
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_path.exists():
            self._create_empty()

    def _create_empty(self):
        data = {
            "owner": "Raphael",
            "memory_version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "policies": {
                "storage_rules": "Never store passwords, private keys, API keys, MFA secrets, recovery codes, session tokens, banking credentials. Use secrets manager.",
                "reviewable": True,
                "deletable": True,
                "categories_restrictable": True
            },
            "preferences": {
                "communication_style": "Natural, concise when simple, detailed when technical. Voice-first.",
                "assistant_name": "J.A.R.V.I.S.",
                "wake_phrases": ["JARVIS"],
                "voice_speed": "normal",
                "preferred_language": "en"
            },
            "projects": [],
            "workflows": [],
            "device_names": {},
            "infrastructure": {},
            "learning_goals": [],
            "non_sensitive_reminders": [],
            "contacts": [],  # Only non-sensitive contact names, not numbers
            "routines": {
                "morning": {"enabled": False, "steps": []},
                "night": {"enabled": False, "steps": []}
            }
        }
        with open(self.memory_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> Dict[str, Any]:
        with open(self.memory_path) as f:
            return json.load(f)

    def _is_forbidden(self, key: str, value: str) -> bool:
        combined = f"{key} {value}".lower()
        return any(forbidden in combined for forbidden in FORBIDDEN_MEMORY_KEYS)

    def add_preference(self, key: str, value: Any, category: str = "preferences") -> bool:
        if self._is_forbidden(key, str(value)):
            audit.log(
                identity="JARVIS",
                device="memory",
                action="MEMORY_REJECTED_FORBIDDEN",
                target=key,
                risk="HIGH",
                auth_decision="DENIED",
                tool="memory",
                result="REJECTED",
                verification="Forbidden key detected - secrets must go to secrets manager",
                notes=f"Attempt to store forbidden category: {key}"
            )
            return False

        data = self.load()
        if category not in data:
            data[category] = {}
        if isinstance(data[category], dict):
            data[category][key] = value
        else:
            data[category].append({key: value})

        with open(self.memory_path, "w") as f:
            json.dump(data, f, indent=2)

        audit.log(
            identity="Raphael",
            device="memory",
            action=f"MEMORY_ADD:{category}:{key}",
            target=category,
            risk="LOW",
            auth_decision="ALLOWED",
            tool="memory",
            result="SUCCESS",
            verification="Non-sensitive memory stored"
        )
        return True

    def get(self, category: str, key: str = None) -> Any:
        data = self.load()
        if key is None:
            return data.get(category, {})
        return data.get(category, {}).get(key)

    def delete(self, category: str, key: str = None) -> bool:
        data = self.load()
        if key is None:
            if category in data:
                del data[category]
        else:
            if category in data and isinstance(data[category], dict):
                data[category].pop(key, None)
        
        with open(self.memory_path, "w") as f:
            json.dump(data, f, indent=2)
        
        audit.log(
            identity="Raphael",
            device="memory",
            action=f"MEMORY_DELETE:{category}:{key}",
            target=category,
            risk="LOW",
            auth_decision="ALLOWED",
            tool="memory",
            result="SUCCESS",
            verification="Memory deleted per owner request"
        )
        return True

    def review(self) -> Dict[str, Any]:
        data = self.load()
        # Return without sensitive fields, with counts
        return {
            "owner": data.get("owner"),
            "version": data.get("memory_version"),
            "categories": list(data.keys()),
            "preferences_count": len(data.get("preferences", {})),
            "projects_count": len(data.get("projects", [])),
            "contacts_count": len(data.get("contacts", [])),
            "policies": data.get("policies")
        }

memory = PersonalMemory()
