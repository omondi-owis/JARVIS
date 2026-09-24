"""
Cybersecurity Monitoring - Production
Correlates Wazuh, system logs, network, for incident detection
Distinguishes Observed/Suspected/Confirmed/Remediated
"""
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from ..core.audit import audit

class SecurityEvent:
    def __init__(self, event_type: str, severity: str, source: str, description: str, raw: Dict = None):
        self.event_type = event_type
        self.severity = severity  # low, medium, high, critical
        self.source = source  # wazuh, system, network, etc.
        self.description = description
        self.raw = raw or {}
        self.timestamp = datetime.now(timezone.utc)
        self.status = "observed"  # observed, suspected, confirmed, remediated
        self.correlated = []

class SecurityMonitor:
    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.thresholds = {
            "failed_ssh_last_5m": 5,
            "wazuh_critical_last_1h": 1
        }

    def add_event(self, event: SecurityEvent):
        self.events.append(event)
        # Keep only last 1000
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
        
        audit.log(
            identity="JARVIS",
            device="security_monitor",
            action=f"SECURITY_EVENT:{event.event_type}:{event.severity}",
            target=event.source,
            risk="HIGH" if event.severity in ["high", "critical"] else "MEDIUM",
            auth_decision="ALLOWED",
            tool="security_monitor",
            result=event.status.upper(),
            verification=f"Event {event.event_type} from {event.source}: {event.description[:200]}"
        )

    def correlate_events(self) -> List[Dict[str, Any]]:
        # Simple correlation - in production use SIEM logic
        now = datetime.now(timezone.utc)
        recent = [e for e in self.events if now - e.timestamp < timedelta(hours=1)]
        
        correlations = []
        
        # Failed SSH brute force
        failed_ssh = [e for e in recent if e.event_type == "failed_ssh"]
        if len(failed_ssh) >= self.thresholds["failed_ssh_last_5m"]:
            correlations.append({
                "type": "possible_brute_force",
                "severity": "high",
                "status": "suspected",
                "events_count": len(failed_ssh),
                "description": f"{len(failed_ssh)} failed SSH attempts in last hour - possible brute force",
                "recommendation": "Check fail2ban, consider blocking IP, review auth logs",
                "events": [e.description for e in failed_ssh[-5:]]
            })
        
        # Wazuh critical
        wazuh_critical = [e for e in recent if e.source == "wazuh" and e.severity == "critical"]
        if len(wazuh_critical) >= self.thresholds["wazuh_critical_last_1h"]:
            correlations.append({
                "type": "wazuh_critical_alerts",
                "severity": "critical",
                "status": "observed",
                "events_count": len(wazuh_critical),
                "description": f"{len(wazuh_critical)} critical Wazuh alerts in last hour",
                "recommendation": "Investigate Wazuh alerts immediately via JARVIS Wazuh integration"
            })
        
        return correlations

    def get_status(self, hours: int = 24) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        recent = [e for e in self.events if now - e.timestamp < timedelta(hours=hours)]
        
        by_severity = {}
        by_source = {}
        by_status = {}
        
        for e in recent:
            by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
            by_source[e.source] = by_source.get(e.source, 0) + 1
            by_status[e.status] = by_status.get(e.status, 0) + 1
        
        correlations = self.correlate_events()
        
        return {
            "period_hours": hours,
            "total_events": len(recent),
            "by_severity": by_severity,
            "by_source": by_source,
            "by_status": by_status,
            "correlations": correlations,
            "critical_count": by_severity.get("critical", 0),
            "message": f"{len(recent)} security events in last {hours}h, {by_severity.get('critical', 0)} critical, {len(correlations)} correlations"
        }

    def investigate(self, event_type: str = None) -> Dict[str, Any]:
        # Deep dive
        filtered = self.events
        if event_type:
            filtered = [e for e in self.events if e.event_type == event_type]
        
        return {
            "filtered_count": len(filtered),
            "latest": [
                {
                    "type": e.event_type,
                    "severity": e.severity,
                    "source": e.source,
                    "description": e.description,
                    "timestamp": e.timestamp.isoformat(),
                    "status": e.status
                }
                for e in filtered[-20:]
            ],
            "correlations": self.correlate_events()
        }

security_monitor = SecurityMonitor()
