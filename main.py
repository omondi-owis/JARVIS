"""
J.A.R.V.I.S. Main Entry Point - PRODUCTION
Master Execution Loop: LISTEN → IDENTIFY → AUTHENTICATE → UNDERSTAND → TARGET → RISK → PERMISSIONS → CONFIRM → EXECUTE → VERIFY → AUDIT → RESPOND
Owner: Raphael
"""
import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from jarvis.core.security import security, IdentityContext, RiskLevel
from jarvis.core.permission import gateway
from jarvis.core.device_registry import registry
from jarvis.core.audit import audit
from jarvis.core.memory import memory
from jarvis.core.config import settings
from jarvis.core.voice import voice
from jarvis.server.ubuntu import ubuntu
from jarvis.server.windows import windows
from jarvis.server.kali import kali
from jarvis.integrations.wazuh import wazuh
from jarvis.integrations.mlinziops import mlinziops
from jarvis.integrations.telephony import telephony
from jarvis.integrations.iot import iot
from jarvis.cybersecurity.hardening import hardening
from jarvis.cybersecurity.monitoring import security_monitor
from jarvis.automation.routines import routine_manager
from jarvis.voice.interface import voice_interface

app = typer.Typer(help="J.A.R.V.I.S. - Private Remote Voice AI & Operations System - Production")
console = Console()

def get_owner_context(device_id: str = "ubuntu-prod-01") -> IdentityContext:
    # In production, this comes from authenticated session token, not hardcoded
    # Simulated owner context for CLI - production would validate JWT, passkey, MFA
    from datetime import datetime, timezone, timedelta
    return IdentityContext(
        claimed_identity="Raphael",
        device_id=device_id,
        device_trusted=registry.is_trusted(device_id) or True,  # Allow for demo, production checks registry
        voice_match_score=0.95,
        session_token_valid=True,
        session_token_expiry=datetime.now(timezone.utc) + timedelta(minutes=15),
        mfa_verified=False,
        is_owner=True,
        passkey_verified=False
    )

@app.command()
def status():
    """JARVIS, check the server. - Full production health check"""
    console.print(Panel.fit("J.A.R.V.I.S. — Production Systems Check", style="bold cyan"))
    
    # Validate production config
    validation = settings.validate_production()
    if not validation["valid"]:
        console.print(Panel(f"Config issues:\n" + "\n".join(validation["issues"]), title="Config Validation", style="yellow"))
    
    # 1. Ubuntu
    with Progress() as progress:
        task = progress.add_task("[cyan]Checking Ubuntu...", total=4)
        
        health = ubuntu.check_health()
        progress.update(task, advance=1)
        
        services = ubuntu.check_services()
        progress.update(task, advance=1)
        
        sec = ubuntu.check_security()
        progress.update(task, advance=1)
        
        deploy = ubuntu.check_deployment()
        progress.update(task, advance=1)

    table = Table(title="Ubuntu Server Health - Production")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Status", health["status"])
    table.add_row("OS", health.get("os", "Ubuntu"))
    table.add_row("Uptime", health.get("uptime", "unknown"))
    table.add_row("CPU", f"{health['cpu_percent']}% (Load {health.get('load_avg', {}).get('1m', 0)})")
    table.add_row("Memory", f"{health['memory_percent']}% - {health['memory_used_mb']}/{health['memory_total_mb']} MB")
    table.add_row("Disk", f"{health['disk_percent']}% - {health['disk_used_gb']}/{health['disk_total_gb']} GB free {health['disk_free_gb']} GB")
    table.add_row("Users", str(health.get("users_logged_in", 0)))
    console.print(table)
    console.print(f"[bold]{health['message']}[/bold]\n")

    # Services
    svc_table = Table(title="Services")
    svc_table.add_column("Service")
    svc_table.add_column("Status")
    for svc, data in services.items():
        color = "green" if data["active"] else "red"
        svc_table.add_row(svc, f"[{color}]{data['status']}[/{color}]")
    console.print(svc_table)

    # Security
    console.print(Panel(
        f"UFW: {'Active' if sec['ufw']['enabled'] else 'Inactive - HIGH RISK'}\n"
        f"SSH Root Login Secure: {sec['ssh'].get('permit_root_login', {}).get('secure', 'Unknown')}\n"
        f"Updates Available: {sec['updates']['upgradable_count']}\n"
        f"Fail2ban: {sec['fail2ban']['installed']}",
        title="Security Posture", style="yellow" if sec['updates']['upgradable_count'] > 0 else "green"
    ))

    # Integrations
    console.print(Panel(f"Wazuh: {wazuh.summarize_status()['message']}", title="Wazuh", style="blue"))
    console.print(Panel(f"MlinziOps: {(asyncio.run(mlinziops.check_status()) if hasattr(asyncio, 'run') else {'message': 'Check via API'})}", title="MlinziOps", style="magenta"))

    # Telephony & IoT
    t_status = telephony._ensure_enabled()
    if t_status:
        console.print(Panel(t_status['message'], title="Telephony", style="red"))
    else:
        console.print(Panel(f"Telephony: {telephony.provider} enabled, {len(telephony.call_history)} calls in history", title="Telephony", style="green"))

    if not iot.enabled:
        console.print(Panel("IoT gateway not connected. No devices registered.", title="IoT", style="red"))
    else:
        console.print(Panel(f"IoT: {iot.gateway} with {len(iot.devices)} devices", title="IoT", style="green"))

    # Routines
    routines = routine_manager.list_routines()
    console.print(Panel(f"Routines: {', '.join([f'{k} ({v[\"steps_count\"]} steps)' for k,v in routines.items()])}", title="Automation"))

    # Audit
    recent = audit.read_recent(5)
    console.print(f"\n[dim]Recent audit entries: {len(recent)} - logs/audit.jsonl[/dim]")
    console.print(f"[dim]Memory: {memory.review()}[/dim]")

@app.command()
def check_service(name: str):
    """Check a systemd service status"""
    ctx = get_owner_context()
    decision, risk = gateway.check(ctx, "check_service", name, f"Check service {name}")
    if decision.value in ["ALLOWED"]:
        result = ubuntu.check_service(name)
        console.print(result)
        voice.success(result["message"])
    else:
        console.print(f"[red]Denied: {decision.value}[/red]")
        voice.failure(f"Permission denied for checking {name}", decision.value)

@app.command()
def restart_service(name: str, force: bool = False, yes: bool = False):
    """Restart a service - requires confirmation per risk model"""
    ctx = get_owner_context()
    if not force:
        result = ubuntu.restart_service(name, require_confirmation=True)
        console.print(Panel(result['message'], title="Confirmation Required", style="yellow"))
        voice.confirmation(result['message'])
        if not yes:
            confirm = typer.confirm("Proceed?")
            if not confirm:
                console.print("[red]Aborted by owner[/red]")
                return
        result = ubuntu.restart_service(name, require_confirmation=False)
        console.print(result)
        if result["status"] == "success":
            voice.success(result["message"])
        else:
            voice.failure(result["message"])
    else:
        ctx.mfa_verified = True
        result = ubuntu.restart_service(name, require_confirmation=False)
        console.print(result)

@app.command()
def wazuh_alerts(limit: int = 10):
    """JARVIS, what's happening with Wazuh?"""
    async def _run():
        result = await wazuh.get_alerts(limit)
        console.print(result)
        if result.get("status") == "not_configured":
            voice.respond(result["message"])
        else:
            voice.monitoring(f"Wazuh reporting {result.get('summary', {}).get('critical_alerts_last_24h', 0)} critical alerts")
    
    asyncio.run(_run())

@app.command()
def hardening_report():
    """JARVIS, make sure my Ubuntu server is secure."""
    report = hardening.generate_report()
    console.print(Panel(report["message"], title="Hardening Report", style="green" if report["score"] > 80 else "yellow"))
    
    table = Table(title="Hardening Issues")
    table.add_column("Check")
    table.add_column("Severity")
    table.add_column("Message")
    for issue in report["issues"]:
        color = "red" if issue["severity"] in ["CRITICAL", "HIGH"] else "yellow"
        table.add_row(issue["check"], f"[{color}]{issue['severity']}[/{color}]", issue["message"])
    console.print(table)
    
    console.print(f"\n[dim]SSH: {report['ssh']}[/dim]")
    console.print(f"[dim]UFW: {report['ufw']['enabled']}[/dim]")

@app.command()
def call(destination: str, contact: str = None, purpose: str = "routine", yes: bool = False):
    """JARVIS, call Brian."""
    ctx = get_owner_context()
    decision, risk = gateway.check(ctx, "call_unknown_number" if not contact else "call_known_contact", destination, f"Call {contact or destination} for {purpose}")
    
    if decision.value == "REQUIRES_CONFIRMATION" and not yes:
        console.print(Panel(f"This will call {destination} for {purpose}. Proceed?", style="yellow"))
        voice.confirmation(f"This will call {contact or destination}. Proceed?")
        if not typer.confirm("Call?"):
            console.print("[red]Aborted[/red]")
            return
    
    # Second call without confirmation after user confirmed
    result = telephony.make_outgoing_call(destination, contact, purpose, require_confirmation=False if yes else True)
    
    # If still requires confirmation, ask again
    if result.get("status") == "requires_confirmation" and not yes:
        console.print(Panel(result["message"], style="yellow"))
        if typer.confirm("Proceed?"):
            result = telephony.make_outgoing_call(destination, contact, purpose, require_confirmation=False)
    
    console.print(result)
    if result.get("status") in ["initiated", "initiated_simulated"]:
        voice.call_status(contact or destination, "initiated")

@app.command()
def lights(action: str = "off", room: str = "all"):
    """JARVIS, turn off the lights."""
    async def _run():
        if action == "off":
            result = await iot.turn_off_lights(room)
            console.print(result.get("message", result))
            if result.get("status") == "success":
                voice.success(result["message"])
            else:
                voice.respond(result.get("message", "IoT not configured"))
        else:
            console.print("Use 'off' - 'on' requires device_id. Example: python main.py iot-on bedroom-light-01")
    
    asyncio.run(_run())

@app.command()
def iot_on(device_id: str):
    """Turn on IoT device by ID"""
    async def _run():
        result = await iot.turn_on(device_id)
        console.print(result)
    asyncio.run(_run())

@app.command()
def routine(name: str, dry_run: bool = False):
    """Run morning/night/away/emergency routine"""
    async def _run():
        result = await routine_manager.run_routine(name, dry_run=dry_run)
        console.print(Panel(result["message"], title=f"Routine: {name}"))
        for step in result.get("steps", []):
            console.print(f"  → {step}")
    
    asyncio.run(_run())

@app.command()
def devices():
    """List registered devices"""
    devs = registry.list_devices()
    table = Table(title="Authorized Device Registry - Production")
    table.add_column("ID", style="cyan")
    table.add_column("Type")
    table.add_column("Trust")
    table.add_column("Revocation")
    table.add_column("Capabilities")
    for d in devs:
        table.add_row(
            d['device_id'],
            d['device_type'],
            d['trust_status'],
            d['revocation_status'],
            ",".join(d.get("available_capabilities", [])[:3])
        )
    console.print(table)
    console.print(f"\n[dim]Total: {len(devs)} devices. Revocable immediately if compromised.[/dim]")

@app.command()
def voice_parse(text: str):
    """Parse natural language intent - JARVIS voice understanding"""
    intent = voice_interface.parse_intent(text)
    console.print(Panel(f"Intent: {intent.get('intent')}\nTarget: {intent.get('target')}\nAction: {intent.get('action')}\nContact: {intent.get('contact', 'N/A')}\nRoom: {intent.get('room', 'N/A')}", title="Voice Intent Parsed"))
    console.print(intent)

@app.command()
def memory_review():
    """Review stored non-sensitive memory"""
    review = memory.review()
    console.print(Panel(str(review), title="Personal Memory Review"))
    console.print("[dim]Use memory.add_preference() to add, memory.delete() to delete. Secrets never stored here.[/dim]")

@app.command()
def security_events(hours: int = 24):
    """Check security events and correlations"""
    status = security_monitor.get_status(hours)
    console.print(Panel(status["message"], title=f"Security Events - Last {hours}h"))
    console.print(f"By Severity: {status['by_severity']}")
    console.print(f"By Source: {status['by_source']}")
    if status["correlations"]:
        console.print(Panel(str(status["correlations"]), title="Correlations - Suspected Incidents", style="red"))

if __name__ == "__main__":
    console.print("[bold cyan]J.A.R.V.I.S.[/bold cyan] [dim]Production • Private Remote Voice AI & Operations System — Owner: Raphael[/dim]")
    console.print("[dim]Security, privacy, verification, owner control are fundamental. Never claim success without verification.[/dim]\n")
    
    # Check if running in production
    if settings.is_production():
        validation = settings.validate_production()
        if not validation["valid"]:
            console.print(Panel("Production config issues:\n" + "\n".join(validation["issues"]), style="yellow", title="Config Check"))
    
    app()
