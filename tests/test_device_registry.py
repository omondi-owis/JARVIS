"""
Tests for Device Registry
"""
import json
import tempfile
from pathlib import Path
from jarvis.core.device_registry import DeviceRegistry

def test_device_registry():
    with tempfile.TemporaryDirectory() as tmp:
        registry_path = Path(tmp) / "device_registry.json"
        registry = DeviceRegistry(str(registry_path))
        
        device = {
            "device_id": "test-01",
            "identity": "Test Device",
            "owner": "Raphael",
            "trust_status": "trusted",
            "device_type": "ubuntu_server",
            "operating_system": "Ubuntu 22.04",
            "available_capabilities": ["bash"],
            "permission_scope": "test",
            "revocation_status": "active"
        }
        
        registry.register_device(device)
        assert registry.is_trusted("test-01") == True
        
        loaded = registry.get_device("test-01")
        assert loaded["device_id"] == "test-01"
        
        registry.revoke_device("test-01")
        assert registry.is_trusted("test-01") == False
