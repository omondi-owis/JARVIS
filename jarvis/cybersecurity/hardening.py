"""
Linux Hardening - Production
Implements CIS benchmarks, SSH hardening, UFW, fail2ban, etc.
"""
import subprocess
from typing import Dict, Any, List
from ..core.audit import audit

class Hardening:
    def __init__(self):
        self.checks = {
            "ssh_root_login": {"description": "SSH PermitRootLogin should be no", "risk": "HIGH"},
            "ssh_password_auth": {"description": "SSH PasswordAuthentication should be no", "risk": "HIGH"},
            "ufw_enabled": {"description": "UFW firewall should be active", "risk": "HIGH"},
            "auto_updates": {"description": "Automatic security updates enabled", "risk": "MEDIUM"},
            "fail2ban": {"description": "Fail2ban should be active", "risk": "MEDIUM"}
        }

    def _run(self, cmd: List[str], timeout: int = 10) -> Dict[str, Any]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_ssh_hardening(self) -> Dict[str, Any]:
        results = {}
        try:
            with open("/etc/ssh/sshd_config") as f:
                content = f.read()
                results["permit_root_login"] = {
                    "secure": "PermitRootLogin no" in content,
                    "current": next((l for l in content.split("\n") if "PermitRootLogin" in l), "Not set"),
                    "recommendation": "PermitRootLogin no"
                }
                results["password_auth"] = {
                    "secure": "PasswordAuthentication no" in content,
                    "current": next((l for l in content.split("\n") if "PasswordAuthentication" in l), "Not set"),
                    "recommendation": "PasswordAuthentication no - use keys"
                }
                results["port"] = {
                    "current": next((l for l in content.split("\n") if l.strip().startswith("Port")), "Port 22"),
                    "recommendation": "Consider non-standard port"
                }
        except Exception as e:
            results["error"] = str(e)
        
        return results

    def check_ufw(self) -> Dict[str, Any]:
        res = self._run(["sudo", "ufw", "status", "verbose"])
        return {
            "enabled": "Status: active" in res["stdout"],
            "rules": res["stdout"][:2000],
            "recommendation": "Allow only necessary ports: 22, 80, 443, plus Wazuh, MlinziOps via Tailscale"
        }

    def check_users(self) -> Dict[str, Any]:
        # Check for users with UID 0, sudo group, etc.
        res_passwd = self._run(["cat", "/etc/passwd"])
        res_sudo = self._run(["getent", "group", "sudo"])
        
        users = []
        for line in res_passwd["stdout"].split("\n"):
            if line:
                parts = line.split(":")
                if len(parts) >= 3 and parts[2] == "0" and parts[0] != "root":
                    users.append({"user": parts[0], "issue": "UID 0 - should only be root", "risk": "CRITICAL"})
        
        return {
            "uid_0_users": users,
            "sudo_group": res_sudo["stdout"],
            "recommendation": "Only authorized users in sudo, no extra UID 0"
        }

    def generate_report(self) -> Dict[str, Any]:
        ssh = self.check_ssh_hardening()
        ufw = self.check_ufw()
        users = self.check_users()
        
        issues = []
        if not ssh.get("permit_root_login", {}).get("secure"):
            issues.append({"check": "ssh_root_login", "severity": "HIGH", "message": "PermitRootLogin not set to no"})
        if not ufw.get("enabled"):
            issues.append({"check": "ufw_enabled", "severity": "HIGH", "message": "UFW not active"})
        if users.get("uid_0_users"):
            issues.append({"check": "uid_0", "severity": "CRITICAL", "message": f"Extra UID 0 users: {users['uid_0_users']}"})
        
        report = {
            "timestamp": "now",
            "ssh": ssh,
            "ufw": ufw,
            "users": users,
            "issues": issues,
            "score": max(0, 100 - len(issues)*15),
            "message": f"Hardening score: {max(0, 100 - len(issues)*15)}/100 - {len(issues)} issues found"
        }
        
        audit.log(
            identity="JARVIS",
            device="ubuntu-prod",
            action="HARDENING_REPORT",
            target="ubuntu-server",
            risk="LOW",
            auth_decision="ALLOWED",
            tool="hardening",
            result="SUCCESS",
            verification=f"Report generated - {len(issues)} issues, score {report['score']}"
        )
        
        return report

    def apply_hardening(self, check_name: str, dry_run: bool = True) -> Dict[str, Any]:
        # Never auto-apply without explicit confirmation and dry-run first
        if dry_run:
            return {
                "status": "dry_run",
                "check": check_name,
                "message": f"Dry run for {check_name} - would apply hardening. Set dry_run=False to apply with confirmation.",
                "requires_confirmation": True
            }
        
        audit.log(
            identity="Raphael",
            device="ubuntu-prod",
            action=f"HARDENING_APPLY:{check_name}",
            target="ubuntu-server",
            risk="HIGH",
            auth_decision="REQUIRES_CONFIRMATION",
            tool="hardening",
            result="PENDING_CONFIRMATION",
            verification=f"Applying hardening {check_name} is high-risk"
        )
        
        return {
            "status": "requires_confirmation",
            "message": f"Applying {check_name} will change security configuration. Proceed?",
            "risk": "HIGH"
        }

hardening = Hardening()
