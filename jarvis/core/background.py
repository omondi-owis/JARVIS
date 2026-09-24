"""
J.A.R.V.I.S. Background Monitoring
Continuously monitors authorized systems when explicitly enabled
Prioritizes: Critical security events > Service outages > High-risk failures > Operational > Routine
"""
import asyncio
import time
from typing import Dict, List, Callable
from datetime import datetime, timezone
from .audit import audit

class BackgroundMonitor:
    def __init__(self):
        self.enabled = False
        self.tasks: List[Dict] = []
        self.alert_callbacks: List[Callable] = []
        self.thresholds = {
            "cpu_percent": 85,
            "memory_percent": 85,
            "disk_percent": 85,
            "service_down_critical": True
        }
        self.last_checks: Dict[str, Dict] = {}

    def enable(self):
        self.enabled = True
        audit.log(
            identity="Raphael",
            device="background_monitor",
            action="BACKGROUND_MONITOR_ENABLE",
            target="all_systems",
            risk="LOW",
            auth_decision="ALLOWED",
            tool="background_monitor",
            result="SUCCESS",
            verification="Background monitoring enabled per explicit owner authorization"
        )

    def disable(self):
        self.enabled = False
        audit.log(
            identity="Raphael",
            device="background_monitor",
            action="BACKGROUND_MONITOR_DISABLE",
            target="all_systems",
            risk="LOW",
            auth_decision="ALLOWED",
            tool="background_monitor",
            result="SUCCESS",
            verification="Background monitoring disabled"
        )

    def add_task(self, name: str, check_func: Callable, interval_seconds: int, priority: int = 5):
        """
        priority: 1=critical security, 2=service outage, 3=high-risk failure, 4=operational, 5=routine
        """
        self.tasks.append({
            "name": name,
            "check_func": check_func,
            "interval": interval_seconds,
            "priority": priority,
            "last_run": 0,
            "failures": 0
        })

    def add_alert_callback(self, callback: Callable):
        self.alert_callbacks.append(callback)

    async def _run_task(self, task: Dict):
        try:
            result = await task["check_func"]() if asyncio.iscoroutinefunction(task["check_func"]) else task["check_func"]()
            
            self.last_checks[task["name"]] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "status": "ok"
            }
            
            # Check thresholds and trigger alerts
            if isinstance(result, dict):
                if result.get("cpu_percent", 0) > self.thresholds["cpu_percent"]:
                    await self._trigger_alert(3, f"High CPU: {result['cpu_percent']}%", result)
                if result.get("memory_percent", 0) > self.thresholds["memory_percent"]:
                    await self._trigger_alert(3, f"High Memory: {result['memory_percent']}%", result)
                if result.get("disk_percent", 0) > self.thresholds["disk_percent"]:
                    await self._trigger_alert(2, f"High Disk: {result['disk_percent']}%", result)
                if result.get("status") == "down" and self.thresholds["service_down_critical"]:
                    await self._trigger_alert(2, f"Service down: {task['name']}", result)
                if "critical_alerts" in result and result["critical_alerts"]:
                    await self._trigger_alert(1, f"Critical security events: {len(result['critical_alerts'])}", result)

            task["failures"] = 0
            
        except Exception as e:
            task["failures"] += 1
            self.last_checks[task["name"]] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "status": "failed",
                "failures": task["failures"]
            }
            if task["failures"] >= 3:
                await self._trigger_alert(2, f"Task {task['name']} failing repeatedly: {str(e)}", {"failures": task["failures"]})

    async def _trigger_alert(self, priority: int, message: str, data: Dict):
        # Priority 1 = Critical security, 2 = Service outage, etc.
        audit.log(
            identity="JARVIS",
            device="background_monitor",
            action=f"ALERT_P{priority}:{message[:100]}",
            target="owner_notification",
            risk="HIGH" if priority <= 2 else "MEDIUM",
            auth_decision="ALLOWED",
            tool="background_monitor",
            result="ALERT_TRIGGERED",
            verification=f"Priority {priority} alert",
            notes=str(data)[:500]
        )
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(priority, message, data)
                else:
                    callback(priority, message, data)
            except Exception as e:
                print(f"Alert callback failed: {e}")

    async def run_forever(self):
        self.enable()
        print("J.A.R.V.I.S. Background monitoring started - prioritizing critical events")
        while self.enabled:
            now = time.time()
            # Sort by priority (lower number = higher priority)
            sorted_tasks = sorted(self.tasks, key=lambda x: x["priority"])
            
            for task in sorted_tasks:
                if now - task["last_run"] >= task["interval"]:
                    await self._run_task(task)
                    task["last_run"] = now
            
            await asyncio.sleep(1)

    def get_status(self) -> Dict:
        return {
            "enabled": self.enabled,
            "tasks_count": len(self.tasks),
            "last_checks": self.last_checks,
            "thresholds": self.thresholds
        }

monitor = BackgroundMonitor()
