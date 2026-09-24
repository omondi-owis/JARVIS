"""
Kali Linux Security Lab - Production
For authorized security learning, vulnerability assessment, lab testing
All testing within explicitly authorized environments only
"""
import subprocess
from typing import Dict, Any, List
from ..core.audit import audit

class KaliLab:
    def __init__(self):
        self.enabled = False
        self.authorized_targets: List[str] = []  # Only these targets allowed for scanning

    def _check_enabled(self):
        if not self.enabled:
            return {
                "status": "not_configured",
                "message": "Kali lab agent not connected. Requires secure agent installation.",
                "authorized_only": "All security testing must remain within explicitly authorized environments"
            }
        return None

    def set_authorized_targets(self, targets: List[str]):
        self.authorized_targets = targets
        audit.log(
            identity="Raphael",
            device="kali_lab",
            action="SET_AUTHORIZED_TARGETS",
            target=",".join(targets),
            risk="MEDIUM",
            auth_decision="ALLOWED",
            tool="kali_lab",
            result="SUCCESS",
            verification=f"Authorized targets set: {len(targets)}"
        )

    def is_target_authorized(self, target: str) -> bool:
        # Check if target is in authorized list or is lab network
        if not self.authorized_targets:
            return False
        # Simple check - production should use CIDR matching, etc.
        return any(auth in target or target in auth for auth in self.authorized_targets)

    def nmap_scan(self, target: str, scan_type: str = "-sV") -> Dict[str, Any]:
        if not self.is_target_authorized(target):
            audit.log(
                identity="Raphael",
                device="kali_lab",
                action="NMAP_UNAUTHORIZED_TARGET",
                target=target,
                risk="HIGH",
                auth_decision="DENIED",
                tool="nmap",
                result="DENIED",
                verification=f"Target {target} not in authorized list: {self.authorized_targets}"
            )
            return {
                "status": "denied",
                "message": f"Target {target} is not authorized for scanning. Authorized: {self.authorized_targets}",
                "risk": "HIGH"
            }
        
        disabled = self._check_enabled()
        if disabled:
            return disabled
        
        # In production, run via agent with proper sandboxing
        audit.log(
            identity="Raphael",
            device="kali_lab",
            action=f"NMAP_SCAN:{scan_type}",
            target=target,
            risk="MEDIUM",
            auth_decision="ALLOWED",
            tool="nmap",
            result="ATTEMPT",
            verification=f"Nmap {scan_type} on authorized target {target}"
        )
        
        try:
            # Example: nmap -sV authorized_target
            # In production, use python-nmap or subprocess with timeouts and output parsing
            cmd = ["nmap", scan_type, target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "status": "success",
                "target": target,
                "scan_type": scan_type,
                "output": result.stdout[:5000],
                "message": f"Nmap scan completed for authorized target {target}"
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def check_tools(self) -> Dict[str, Any]:
        tools = ["nmap", "wireshark", "burpsuite", "metasploit", "nikto", "gobuster", "wpscan"]
        results = {}
        for tool in tools:
            res = subprocess.run(["which", tool], capture_output=True, text=True)
            results[tool] = {"installed": res.returncode == 0, "path": res.stdout.strip()}
        return results

    def wireshark_capture(self, interface: str = "eth0", duration: int = 10) -> Dict[str, Any]:
        if not self.enabled:
            return self._check_enabled()
        
        audit.log(
            identity="Raphael",
            device="kali_lab",
            action="WIRESHARK_CAPTURE",
            target=interface,
            risk="MEDIUM",
            auth_decision="REQUIRES_CONFIRMATION",
            tool="wireshark",
            result="PENDING_CONFIRMATION",
            verification=f"Packet capture on {interface} for {duration}s"
        )
        return {
            "status": "requires_confirmation",
            "message": f"This will capture packets on {interface} for {duration} seconds. Proceed?",
            "risk": "MEDIUM"
        }

kali = KaliLab()
