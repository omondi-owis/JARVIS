"""
Device Registry - Authorized infrastructure only
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone

class DeviceRegistry:
    def __init__(self, registry_path: str = "config/device_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self._create_empty()

    def _create_empty(self):
        data = {
            "registry_version": "1.0",
            "owner": "Raphael",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "devices": []
        }
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> Dict:
        with open(self.registry_path) as f:
            return json.load(f)

    def list_devices(self) -> List[Dict]:
        data = self.load()
        return data.get("devices", [])

    def get_device(self, device_id: str) -> Optional[Dict]:
        for d in self.list_devices():
            if d["device_id"] == device_id:
                return d
        return None

    def register_device(self, device: Dict):
        data = self.load()
        # Remove existing if present
        data["devices"] = [d for d in data["devices"] if d["device_id"] != device["device_id"]]
        device["last_seen"] = datetime.now(timezone.utc).isoformat()
        data["devices"].append(device)
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def revoke_device(self, device_id: str) -> bool:
        data = self.load()
        found = False
        for d in data["devices"]:
            if d["device_id"] == device_id:
                d["revocation_status"] = "revoked"
                d["trust_status"] = "revoked"
                found = True
        if found:
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)
        return found

    def is_trusted(self, device_id: str) -> bool:
        dev = self.get_device(device_id)
        if not dev:
            return False
        return dev.get("revocation_status") == "active" and "trusted" in dev.get("trust_status", "")

registry = DeviceRegistry()
