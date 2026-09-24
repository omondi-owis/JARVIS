"""
Smart-Home Automation & Operational Routines - Production
Morning, Night, Away, Emergency with safety checks
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from ..core.audit import audit
from ..server.ubuntu import ubuntu

class RoutineManager:
    def __init__(self):
        self.routines = {
            "morning": {
                "name": "Morning Routine",
                "description": "Authenticate, check systems, activate devices, report alerts",
                "enabled": False,
                "schedule": "07:00",
                "steps": [
                    {"action": "authenticate", "description": "Authenticate Raphael via trusted device", "risk": "LOW"},
                    {"action": "check_system_status", "description": "Check Ubuntu, Wazuh, MlinziOps", "risk": "LOW"},
                    {"action": "activate_devices", "description": "Activate configured lights, thermostat", "risk": "LOW"},
                    {"action": "report_alerts", "description": "Report important overnight alerts", "risk": "LOW"}
                ]
            },
            "night": {
                "name": "Night Routine",
                "description": "Secure home, turn off devices, enable security, check health",
                "enabled": False,
                "schedule": "22:30",
                "steps": [
                    {"action": "check_doors_sensors", "description": "Check registered doors/sensors are closed", "risk": "LOW"},
                    {"action": "turn_off_devices", "description": "Turn off configured lights, plugs", "risk": "LOW"},
                    {"action": "enable_security", "description": "Enable approved security systems, cameras", "risk": "MEDIUM"},
                    {"action": "check_server_health", "description": "Check server health, disk, backups", "risk": "LOW"},
                    {"action": "report_outstanding", "description": "Report outstanding alerts", "risk": "LOW"}
                ]
            },
            "away": {
                "name": "Away Routine",
                "description": "Secure for away - locks, cameras, eco mode",
                "enabled": False,
                "steps": [
                    {"action": "lock_doors", "description": "Lock all registered doors", "risk": "MEDIUM"},
                    {"action": "enable_cameras", "description": "Enable security cameras, alarms", "risk": "MEDIUM"},
                    {"action": "eco_mode", "description": "Set thermostat to eco, off non-essential", "risk": "LOW"},
                    {"action": "notify_anomalies", "description": "Notify if anomalies detected", "risk": "LOW"}
                ]
            },
            "emergency": {
                "name": "Emergency Routine",
                "description": "Emergency - notify, activate emergency systems, contact configured services",
                "enabled": False,
                "requires_confirmation": True,
                "steps": [
                    {"action": "notify_raphael", "description": "Notify Raphael immediately", "risk": "LOW"},
                    {"action": "activate_emergency_lights", "description": "Activate emergency lights", "risk": "LOW"},
                    {"action": "contact_emergency_services", "description": "Contact configured emergency services where authorized", "risk": "HIGH"},
                    {"action": "preserve_logs", "description": "Preserve logs and evidence", "risk": "LOW"}
                ]
            }
        }

    def list_routines(self) -> Dict[str, Any]:
        return {
            name: {
                "name": data["name"],
                "description": data["description"],
                "enabled": data["enabled"],
                "schedule": data.get("schedule"),
                "steps_count": len(data["steps"])
            }
            for name, data in self.routines.items()
        }

    def enable_routine(self, name: str) -> Dict[str, Any]:
        if name not in self.routines:
            return {"status": "not_found", "message": f"Routine {name} not found"}
        
        self.routines[name]["enabled"] = True
        
        audit.log(
            identity="Raphael",
            device="automation",
            action=f"ENABLE_ROUTINE:{name}",
            target=name,
            risk="LOW",
            auth_decision="ALLOWED",
            tool="routines",
            result="SUCCESS",
            verification=f"Routine {name} enabled"
        )
        
        return {"status": "enabled", "routine": name}

    def disable_routine(self, name: str) -> Dict[str, Any]:
        if name not in self.routines:
            return {"status": "not_found"}
        
        self.routines[name]["enabled"] = False
        
        audit.log(
            identity="Raphael",
            device="automation",
            action=f"DISABLE_ROUTINE:{name}",
            target=name,
            risk="LOW",
            auth_decision="ALLOWED",
            tool="routines",
            result="SUCCESS",
            verification=f"Routine {name} disabled"
        )
        
        return {"status": "disabled", "routine": name}

    async def run_routine(self, name: str, dry_run: bool = False) -> Dict[str, Any]:
        if name not in self.routines:
            return {"status": "not_found", "message": f"Routine {name} not found. Available: {list(self.routines.keys())}"}
        
        routine = self.routines[name]
        
        if routine.get("requires_confirmation") and not dry_run:
            audit.log(
                identity="Raphael",
                device="automation",
                action=f"ROUTINE:{name}",
                target=name,
                risk="HIGH",
                auth_decision="REQUIRES_CONFIRMATION",
                tool="routines",
                result="PENDING_CONFIRMATION",
                verification=f"Routine {name} requires confirmation - emergency routine"
            )
            return {
                "status": "requires_confirmation",
                "routine": name,
                "description": routine["description"],
                "message": f"Emergency routine {name} will contact emergency services where configured. Proceed?",
                "risk": "HIGH"
            }
        
        results = []
        for step in routine["steps"]:
            if dry_run:
                results.append({"step": step["action"], "status": "dry_run", "description": step["description"]})
            else:
                # Execute step
                if step["action"] == "check_system_status" or step["action"] == "check_server_health":
                    health = ubuntu.check_health()
                    results.append({"step": step["action"], "status": "success", "result": health["message"]})
                else:
                    results.append({"step": step["action"], "status": "simulated", "description": step["description"]})
        
        audit.log(
            identity="Raphael",
            device="automation",
            action=f"RUN_ROUTINE:{name}",
            target=name,
            risk="MEDIUM" if name in ["away", "emergency"] else "LOW",
            auth_decision="ALLOWED",
            tool="routines",
            result="SUCCESS" if not dry_run else "DRY_RUN",
            verification=f"Routine {name} executed with {len(results)} steps"
        )
        
        return {
            "status": "completed" if not dry_run else "dry_run",
            "routine": name,
            "name": routine["name"],
            "steps": results,
            "message": f"{'Would run' if dry_run else 'Ran'} {name} routine - {len(results)} steps"
        }

routine_manager = RoutineManager()
