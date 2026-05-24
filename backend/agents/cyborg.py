"""
Cyborg.ai — Security, Governance, and Risk Verification

Verifies actions against policy, audits compliance, assesses risk,
enforces kill switches, and checks authorization. This is the trust
enforcement layer of NoblePort OS.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from backend.agents.base import AgentFamily, BaseAgent

logger = logging.getLogger(__name__)

HIGH_RISK_ACTIONS = frozenset({
    "delete_job",
    "void_payment",
    "override_deposit_gate",
    "force_close_job",
    "modify_contract_value",
    "bulk_status_change",
    "export_financial_data",
    "change_permissions",
})

FINANCIAL_THRESHOLD = 50_000.0


class CyborgAgent(BaseAgent):

    def __init__(self) -> None:
        super().__init__(
            name="Cyborg.ai",
            family=AgentFamily.CYBORG,
            role="Security, governance, and risk verification",
            agent_id="cyborg-primary",
        )
        self._kill_switches: dict[str, dict[str, Any]] = {}
        self._policy_rules: list[dict[str, Any]] = [
            {
                "id": "deposit-before-build",
                "rule": "Deposit must be collected before job activation",
                "scope": "job",
                "enforced": True,
            },
            {
                "id": "human-approval-high-value",
                "rule": "Human approval required for actions over $50,000",
                "scope": "financial",
                "enforced": True,
            },
            {
                "id": "permit-before-build",
                "rule": "Permit must be issued before construction (unless exempt)",
                "scope": "permit",
                "enforced": True,
            },
            {
                "id": "dual-approval-refunds",
                "rule": "Refunds require dual approval",
                "scope": "financial",
                "enforced": True,
            },
        ]

    async def _handle_task(
        self, task_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        handlers = {
            "verify_action": self.verify_action,
            "audit_compliance": self.audit_compliance,
            "assess_risk": self.assess_risk,
            "enforce_kill_switch": self.enforce_kill_switch,
            "check_authorization": self.check_authorization,
        }
        handler = handlers.get(task_type)
        if not handler:
            raise ValueError(f"Unknown Cyborg task: {task_type}")
        return await handler(payload)

    # -----------------------------------------------------------------
    # Action Verification
    # -----------------------------------------------------------------

    async def verify_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Verify whether an action should be allowed.

        Checks:
          - Kill switch status for the action's scope
          - High-risk action classification
          - Financial thresholds
          - Policy rule evaluation
        """
        actor = payload.get("actor", "unknown")
        actor_type = payload.get("actor_type", "system")
        action = payload.get("action", "")
        subject = payload.get("subject", "")
        amount = payload.get("amount", 0.0)
        context = payload.get("context", {})

        violations: list[dict[str, str]] = []
        requires_human = False
        blocked = False

        # Check kill switches
        for scope, ks in self._kill_switches.items():
            if ks.get("armed") and (scope == "global" or scope in action):
                blocked = True
                violations.append({
                    "rule": f"kill-switch-{scope}",
                    "detail": f"Kill switch armed for scope: {scope}",
                })

        # High-risk action check
        if action in HIGH_RISK_ACTIONS:
            requires_human = True
            if actor_type == "agent":
                violations.append({
                    "rule": "high-risk-agent-action",
                    "detail": f"Action '{action}' requires human approval when initiated by agent",
                })

        # Financial threshold
        if amount > FINANCIAL_THRESHOLD:
            requires_human = True
            if actor_type != "human":
                violations.append({
                    "rule": "financial-threshold",
                    "detail": f"Amount ${amount:,.2f} exceeds ${FINANCIAL_THRESHOLD:,.2f} threshold",
                })

        # Policy rules
        for rule in self._policy_rules:
            if not rule["enforced"]:
                continue
            if rule["id"] == "deposit-before-build" and action == "activate_job":
                if not context.get("deposit_collected"):
                    blocked = True
                    violations.append({
                        "rule": rule["id"],
                        "detail": rule["rule"],
                    })

        decision = "blocked" if blocked else "requires_approval" if requires_human else "allowed"

        result = {
            "actor": actor,
            "action": action,
            "subject": subject,
            "decision": decision,
            "requires_human_approval": requires_human,
            "violations": violations,
            "violation_count": len(violations),
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "agent": "Cyborg",
        }

        if blocked:
            logger.warning("Action BLOCKED: %s by %s on %s", action, actor, subject)
        elif requires_human:
            logger.info("Action requires approval: %s by %s", action, actor)

        return result

    # -----------------------------------------------------------------
    # Compliance Audit
    # -----------------------------------------------------------------

    async def audit_compliance(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Comprehensive compliance audit for a job."""
        job_id = payload.get("job_id")
        deposit_collected = payload.get("deposit_collected", False)
        permit_issued = payload.get("permit_issued", False)
        insurance_current = payload.get("insurance_current", True)
        contract_signed = payload.get("contract_signed", False)
        change_orders_approved = payload.get("all_cos_approved", True)

        checks = []

        checks.append({
            "check": "deposit_collected",
            "passed": deposit_collected,
            "detail": "Deposit collected before work started" if deposit_collected else "MISSING: Deposit not collected",
        })
        checks.append({
            "check": "permit_issued",
            "passed": permit_issued,
            "detail": "All required permits issued" if permit_issued else "MISSING: Required permits not issued",
        })
        checks.append({
            "check": "insurance_current",
            "passed": insurance_current,
            "detail": "Insurance coverage current" if insurance_current else "WARNING: Insurance may have lapsed",
        })
        checks.append({
            "check": "contract_signed",
            "passed": contract_signed,
            "detail": "Contract signed by all parties" if contract_signed else "MISSING: Contract not signed",
        })
        checks.append({
            "check": "change_orders_approved",
            "passed": change_orders_approved,
            "detail": "All change orders approved" if change_orders_approved else "WARNING: Unapproved change orders",
        })

        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)
        compliance_score = (passed / total * 100) if total > 0 else 0

        return {
            "job_id": job_id,
            "compliance_score": round(compliance_score, 1),
            "status": (
                "compliant" if compliance_score == 100
                else "partially_compliant" if compliance_score >= 60
                else "non_compliant"
            ),
            "checks": checks,
            "passed": passed,
            "total": total,
            "agent": "Cyborg",
        }

    # -----------------------------------------------------------------
    # Risk Assessment
    # -----------------------------------------------------------------

    async def assess_risk(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Assess risk of a proposed action."""
        action_type = payload.get("action_type", "unknown")
        context = payload.get("context", {})
        amount = context.get("amount", 0)

        risk_score = 0
        risk_factors = []

        if action_type in HIGH_RISK_ACTIONS:
            risk_score += 40
            risk_factors.append("High-risk action category")

        if amount > 100_000:
            risk_score += 30
            risk_factors.append(f"High value: ${amount:,.2f}")
        elif amount > FINANCIAL_THRESHOLD:
            risk_score += 15
            risk_factors.append(f"Above threshold: ${amount:,.2f}")

        if context.get("actor_type") == "agent":
            risk_score += 10
            risk_factors.append("Agent-initiated action")

        if not context.get("has_audit_trail", True):
            risk_score += 20
            risk_factors.append("No audit trail for prior actions")

        risk_level = (
            "critical" if risk_score >= 70
            else "high" if risk_score >= 50
            else "medium" if risk_score >= 25
            else "low"
        )

        return {
            "action_type": action_type,
            "risk_level": risk_level,
            "risk_score": min(risk_score, 100),
            "risk_factors": risk_factors,
            "recommendation": (
                "Block without dual human approval" if risk_level == "critical"
                else "Require human approval" if risk_level == "high"
                else "Proceed with logging" if risk_level == "medium"
                else "Proceed normally"
            ),
            "agent": "Cyborg",
        }

    # -----------------------------------------------------------------
    # Kill Switch
    # -----------------------------------------------------------------

    async def enforce_kill_switch(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Arm or disarm a kill switch for a given scope."""
        scope = payload.get("scope", "global")
        armed = payload.get("armed", True)
        reason = payload.get("reason", "")
        controller = payload.get("controller", "system")

        self._kill_switches[scope] = {
            "scope": scope,
            "armed": armed,
            "reason": reason,
            "controller": controller,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
        }

        self._kill_switch_armed = any(
            ks.get("armed", False) for ks in self._kill_switches.values()
        )

        action = "ARMED" if armed else "DISARMED"
        logger.warning("Kill switch %s for scope '%s' by %s: %s", action, scope, controller, reason)

        return {
            "scope": scope,
            "armed": armed,
            "reason": reason,
            "controller": controller,
            "active_kill_switches": [
                ks for ks in self._kill_switches.values() if ks.get("armed")
            ],
            "agent": "Cyborg",
        }

    # -----------------------------------------------------------------
    # Authorization
    # -----------------------------------------------------------------

    async def check_authorization(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Check if an actor is authorized for a resource and permission."""
        actor = payload.get("actor", "")
        resource = payload.get("resource", "")
        permission = payload.get("permission", "read")

        # Simplified RBAC - in production this queries the auth service
        authorized = True
        reason = "Authorized"

        if permission in ("delete", "admin") and not actor.startswith("admin:"):
            authorized = False
            reason = f"Actor '{actor}' lacks '{permission}' permission on '{resource}'"

        return {
            "actor": actor,
            "resource": resource,
            "permission": permission,
            "authorized": authorized,
            "reason": reason,
            "agent": "Cyborg",
        }
