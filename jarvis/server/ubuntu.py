"""
Ubuntu Server Management - PRODUCTION
Full implementation with hardening, monitoring, deployment
Least privilege, auditable, verified
"""
import psutil
import shutil
import subprocess
import os
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone
from ..core.audit import audit

class UbuntuServer:
    def __init__(self):
        self.os_release = self._get_os_release()

    def _get_os_release(self) -> Dict[str, str]:
        try:
            with open("/etc/os-release") as f:
                data = {}
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        data[k] = v.strip('"')
                return data
        except:
            return {"NAME": "Unknown", "VERSION": "Unknown"}

    def _run(self, cmd: List[str], timeout: int = 10, check: bool = False) -> Dict[str, Any]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=check)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout", "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e), "stdout": "", "stderr": str(e)}

    def check_health(self) -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        load = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        try:
            uptime = subprocess.check_output(["uptime", "-p"], text=True).strip()
        except:
            uptime = "unknown"
        
        try:
            users = subprocess.check_output(["who"], text=True).strip().split("\n")
            users_count = len([u for u in users if u.strip()])
        except:
            users_count = 0

        result = {
            "status": "online",
            "os": f"{self.os_release.get('NAME', 'Ubuntu')} {self.os_release.get('VERSION', '')}",
            "uptime": uptime,
            "cpu_percent": cpu,
            "load_avg": {"1m": load[0], "5m": load[1], "15m": load[2]},
            "memory_percent": mem.percent,
            "memory_used_mb": round(mem.used / 1024 / 1024),
            "memory_total_mb": round(mem.total / 1024 / 1024),
            "memory_available_mb": round(mem.available / 1024 / 1024),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "disk_io_read_mb": round(disk_io.read_bytes / 1024 / 1024, 2) if disk_io else 0,
            "disk_io_write_mb": round(disk_io.write_bytes / 1024 / 1024, 2) if disk_io else 0,
            "net_io_sent_mb": round(net_io.bytes_sent / 1024 / 1024, 2) if net_io else 0,
            "net_io_recv_mb": round(net_io.bytes_recv / 1024 / 1024, 2) if net_io else 0,
            "users_logged_in": users_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Ubuntu server is online. CPU {cpu}%, Memory {mem.percent}%, Disk {disk.percent}% used. Uptime: {uptime}"
        }

        audit.log(
            identity="JARVIS",
            device="ubuntu-prod",
            action="CHECK_SERVER_HEALTH",
            target="ubuntu-server",
            risk="LOW",
            auth_decision="ALLOWED",
            tool="psutil",
            result="SUCCESS",
            verification=f"CPU={cpu}%, MEM={mem.percent}%, DISK={disk.percent}%, Load={load[0]}"
        )
        return result

    def check_services(self, services: List[str] = None) -> Dict[str, Any]:
        if services is None:
            services = ["ssh", "ufw", "docker", "nginx", "wazuh-agent", "jarvis"]
        
        results = {}
        for svc in services:
            res = self._run(["systemctl", "is-active", svc], timeout=5)
            active = res["stdout"].strip() if res["success"] or res["stdout"] else "inactive"
            results[svc] = {
                "status": active,
                "active": active == "active",
                "details": res["stdout"][:200]
            }
        
        audit.log(
            identity="JARVIS",
            device="ubuntu-prod",
            action="CHECK_SERVICES",
            target=",".join(services),
            risk="LOW",
            auth_decision="ALLOWED",
            tool="systemctl",
            result="SUCCESS",
            verification=f"Checked {len(services)} services"
        )
        return results

    def check_service(self, service_name: str) -> Dict[str, Any]:
        res = self._run(["systemctl", "is-active", service_name], timeout=5)
        status = res["stdout"].strip() if res["stdout"] else "unknown"
        
        # Get more details
        detail_res = self._run(["systemctl", "status", service_name, "--no-pager", "-l"], timeout=5)
        
        audit.log(
            identity="JARVIS",
            device="ubuntu-prod",
            action=f"CHECK_SERVICE:{service_name}",
            target=service_name,
            risk="LOW",
            auth_decision="ALLOWED",
            tool="systemctl",
            result="SUCCESS",
            verification=f"Service {service_name} is {status}"
        )
        return {
            "service": service_name,
            "status": status,
            "active": status == "active",
            "details": detail_res["stdout"][:1000],
            "message": f"Service {service_name} is {status}"
        }

    def restart_service(self, service_name: str, require_confirmation: bool = True) -> Dict[str, Any]:
        if require_confirmation:
            audit.log(
                identity="Raphael",
                device="ubuntu-prod",
                action=f"RESTART_SERVICE:{service_name}",
                target=service_name,
                risk="MEDIUM",
                auth_decision="REQUIRES_CONFIRMATION",
                tool="systemctl",
                result="PENDING_CONFIRMATION",
                verification=f"This will restart {service_name} and interrupt active services"
            )
            return {
                "status": "requires_confirmation",
                "service": service_name,
                "message": f"This will restart {service_name} and interrupt active services. Proceed?",
                "risk": "MEDIUM"
            }
        
        try:
            # Restart
            restart_res = self._run(["sudo", "systemctl", "restart", service_name], timeout=30)
            if not restart_res["success"]:
                audit.log(
                    identity="Raphael",
                    device="ubuntu-prod",
                    action=f"RESTART_SERVICE:{service_name}",
                    target=service_name,
                    risk="MEDIUM",
                    auth_decision="ALLOWED",
                    tool="systemctl",
                    result="FAILED",
                    verification=f"Restart failed: {restart_res['stderr'][:500]}"
                )
                return {
                    "status": "failed",
                    "service": service_name,
                    "error": restart_res["stderr"][:500],
                    "message": f"The {service_name} service did not restart successfully. The service returned an error during startup. I have not reported the deployment as successful."
                }
            
            # Verify
            verify_res = self._run(["systemctl", "is-active", service_name], timeout=10)
            is_active = verify_res["stdout"].strip() == "active"
            
            audit.log(
                identity="Raphael",
                device="ubuntu-prod",
                action=f"RESTART_SERVICE:{service_name}",
                target=service_name,
                risk="MEDIUM",
                auth_decision="ALLOWED",
                tool="systemctl",
                result="SUCCESS" if is_active else "FAILED",
                verification=f"Service {service_name} restart verification: {verify_res['stdout'].strip()}"
            )
            
            if is_active:
                return {"status": "success", "service": service_name, "message": f"Service {service_name} restarted successfully and is active"}
            else:
                return {"status": "failed", "service": service_name, "message": f"Service {service_name} restarted but is not active: {verify_res['stdout']}"}
                
        except Exception as e:
            audit.log(
                identity="Raphael",
                device="ubuntu-prod",
                action=f"RESTART_SERVICE:{service_name}",
                target=service_name,
                risk="MEDIUM",
                auth_decision="ALLOWED",
                tool="systemctl",
                result="FAILED",
                verification=f"Exception: {str(e)}"
            )
            return {"status": "failed", "service": service_name, "error": str(e)}

    def check_security(self) -> Dict[str, Any]:
        checks = {}
        
        # UFW
        ufw_res = self._run(["sudo", "ufw", "status", "verbose"], timeout=5)
        checks["ufw"] = {
            "raw": ufw_res["stdout"][:1000],
            "enabled": "Status: active" in ufw_res["stdout"],
            "success": ufw_res["success"]
        }
        
        # SSH config
        try:
            with open("/etc/ssh/sshd_config") as f:
                content = f.read()
                checks["ssh"] = {
                    "permit_root_login": "PermitRootLogin no" in content or "PermitRootLogin prohibit-password" in content,
                    "password_auth": "PasswordAuthentication no" in content,
                    "port": next((line.split()[1] for line in content.split("\n") if line.strip().startswith("Port")), "22"),
                    "raw_checks": "sshd_config readable"
                }
        except Exception as e:
            checks["ssh"] = {"error": str(e), "readable": False}
        
        # Fail2ban
        f2b_res = self._run(["sudo", "fail2ban-client", "status"], timeout=5)
        checks["fail2ban"] = {
            "installed": f2b_res["success"],
            "status": f2b_res["stdout"][:500] if f2b_res["success"] else f2b_res["stderr"][:500]
        }
        
        # Updates
        updates_res = self._run(["apt", "list", "--upgradable"], timeout=10)
        upgradable = [line for line in updates_res["stdout"].split("\n") if "/" in line and "upgradable" in line]
        checks["updates"] = {
            "upgradable_count": len(upgradable),
            "upgradable": upgradable[:10],  # First 10
            "needs_update": len(upgradable) > 0
        }
        
        # Users with sudo
        sudo_res = self._run(["getent", "group", "sudo"], timeout=5)
        checks["sudo_users"] = sudo_res["stdout"].strip()
        
        # Listening ports
        ss_res = self._run(["ss", "-tuln"], timeout=5)
        checks["listening_ports"] = ss_res["stdout"][:1000]
        
        audit.log(
            identity="JARVIS",
            device="ubuntu-prod",
            action="CHECK_SECURITY",
            target="ubuntu-server",
            risk="LOW",
            auth_decision="ALLOWED",
            tool="security_check",
            result="SUCCESS",
            verification=f"Security checks: UFW={checks['ufw']['enabled']}, Updates={checks['updates']['upgradable_count']}"
        )
        
        return checks

    def check_logs(self, service: str = None, lines: int = 50) -> Dict[str, Any]:
        if service:
            res = self._run(["journalctl", "-u", service, "-n", str(lines), "--no-pager"], timeout=10)
            return {"service": service, "logs": res["stdout"][-5000:], "success": res["success"]}
        else:
            res = self._run(["journalctl", "-n", str(lines), "--no-pager"], timeout=10)
            return {"logs": res["stdout"][-5000:], "success": res["success"]}

    def check_deployment(self, path: str = "/home/sysadmin/jarvis") -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {"status": "not_found", "path": path}
        
        # Git status
        git_status = self._run(["git", "status", "--porcelain"], timeout=5)
        git_log = self._run(["git", "log", "--oneline", "-5"], timeout=5)
        git_remote = self._run(["git", "remote", "-v"], timeout=5)
        
        # Check if venv exists
        venv_exists = (p / ".venv").exists()
        env_exists = (p / ".env").exists()
        
        return {
            "path": path,
            "exists": True,
            "git_status": git_status["stdout"][:1000],
            "git_clean": len(git_status["stdout"].strip()) == 0,
            "git_log": git_log["stdout"],
            "git_remote": git_remote["stdout"],
            "venv_exists": venv_exists,
            "env_exists": env_exists,
            "env_perms": oct((p / ".env").stat().st_mode)[-3:] if env_exists else "N/A"
        }

ubuntu = UbuntuServer()
