"""
Permission Gateway - Enforces Master Execution Loop
"""
from .security import security, IdentityContext, OperationRequest, RiskLevel, AuthResult
from .audit import audit

class PermissionGateway:
    def check(
        self,
        ctx: IdentityContext,
        capability: str,
        target: str,
        description: str = "",
        privilege: str = "low"
    ) -> tuple[AuthResult, RiskLevel]:
        risk = security.assess_risk(capability, target)
        req = OperationRequest(
            who=ctx.claimed_identity,
            device_id=ctx.device_id,
            capability=capability,
            target=target,
            privilege_required=privilege,
            risk=risk,
            description=description
        )
        decision = security.check_permission_gateway(ctx, req)

        # Audit every check
        audit.log(
            identity=ctx.claimed_identity,
            device=ctx.device_id,
            action=f"PERMISSION_CHECK:{capability}",
            target=target,
            risk=risk.value,
            auth_decision=decision.value,
            tool="permission_gateway",
            result="CHECKED",
            verification=f"Risk={risk.value}, Privilege={privilege}",
            notes=description
        )

        return decision, risk

gateway = PermissionGateway()
