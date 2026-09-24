"""
J.A.R.V.I.S. Configuration Management
Production-level with secrets manager integration, env validation
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class SecurityConfig(BaseModel):
    session_token_ttl_seconds: int = 900
    require_mfa_for_high_risk: bool = True
    max_failed_attempts: int = 5
    lockout_duration_seconds: int = 900
    audit_retention_days: int = 90
    encryption_key_path: Optional[str] = None

class WazuhConfig(BaseModel):
    enabled: bool = False
    api_url: Optional[str] = None
    api_user: Optional[str] = None
    api_port: int = 55000
    verify_ssl: bool = False
    alerts_index: str = "wazuh-alerts-*"

class MlinziOpsConfig(BaseModel):
    enabled: bool = False
    api_url: Optional[str] = None
    timeout_seconds: int = 30

class TelephonyConfig(BaseModel):
    enabled: bool = False
    provider: str = "twilio"  # twilio, asterisk
    caller_id: Optional[str] = None
    recording_consent_required: bool = True
    identify_as_ai: bool = True

class IoTConfig(BaseModel):
    enabled: bool = False
    gateway: str = "mqtt"  # mqtt, homeassistant
    mqtt_broker: Optional[str] = None
    mqtt_port: int = 1883
    homeassistant_url: Optional[str] = None

class TailscaleConfig(BaseModel):
    enabled: bool = False
    auth_key_env: str = "TAILSCALE_AUTHKEY"
    tailnet: Optional[str] = None

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 2
    log_level: str = "INFO"
    environment: str = "production"

class JarvisSettings(BaseSettings):
    # Core
    owner: str = Field(default="Raphael", env="JARVIS_OWNER")
    environment: str = Field(default="production", env="JARVIS_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Paths
    config_path: str = Field(default="config/config.json", env="JARVIS_CONFIG")
    device_registry_path: str = Field(default="config/device_registry.json", env="JARVIS_DEVICE_REGISTRY")
    audit_log_path: str = Field(default="logs/audit.jsonl", env="JARVIS_AUDIT_LOG")
    memory_path: str = Field(default="config/memory.json", env="JARVIS_MEMORY")
    
    # Security
    jwt_secret: Optional[str] = Field(default=None, env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15
    
    # Integrations - loaded from env, never hardcoded
    wazuh_api_url: Optional[str] = Field(default=None, env="WAZUH_API_URL")
    wazuh_api_user: Optional[str] = Field(default=None, env="WAZUH_API_USER")
    wazuh_api_pass: Optional[str] = Field(default=None, env="WAZUH_API_PASS")
    
    mlinziops_api_url: Optional[str] = Field(default=None, env="MLINZIOPS_API_URL")
    mlinziops_api_key: Optional[str] = Field(default=None, env="MLINZIOPS_API_KEY")
    
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    
    mqtt_broker: Optional[str] = Field(default=None, env="MQTT_BROKER")
    mqtt_user: Optional[str] = Field(default=None, env="MQTT_USER")
    mqtt_pass: Optional[str] = Field(default=None, env="MQTT_PASS")
    
    tailscale_authkey: Optional[str] = Field(default=None, env="TAILSCALE_AUTHKEY")

    class Config:
        env_file = ".env"
        extra = "allow"

    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_production(self) -> Dict[str, Any]:
        issues = []
        if self.is_production():
            if not self.jwt_secret or len(self.jwt_secret) < 32:
                issues.append("JWT_SECRET must be set and >=32 chars in production")
            if self.wazuh_api_url and not self.wazuh_api_user:
                issues.append("WAZUH_API_USER required when WAZUH_API_URL set")
            # Check config files exist
            if not Path(self.config_path).exists():
                issues.append(f"Config file missing: {self.config_path} - copy from config.example.json")
        return {"valid": len(issues) == 0, "issues": issues}

settings = JarvisSettings()

def load_json_config(path: str = None) -> Dict[str, Any]:
    cfg_path = Path(path or settings.config_path)
    if not cfg_path.exists():
        example = cfg_path.parent / "config.example.json"
        if example.exists():
            with open(example) as f:
                return json.load(f)
        return {}
    with open(cfg_path) as f:
        return json.load(f)

# Production config loader with secrets scrubbing
def get_safe_config_for_logging() -> Dict[str, Any]:
    cfg = load_json_config()
    # Scrub secrets for logging
    scrubbed = json.dumps(cfg)
    for secret_key in ["password", "secret", "api_key", "auth_token", "private"]:
        # Simple scrub - production should use deeper
        if secret_key in scrubbed.lower():
            cfg = {"note": "Config contains secrets - not shown in logs"}
            break
    return cfg
