"""
NoblePort OS — Agent Mesh Orchestrator

The kernel of the NoblePort operating system. Holds references to all
five agents, routes events intelligently, and provides a unified health
surface for Mission Control.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from backend.agents.base import AgentFamily, AgentHealth, BaseAgent
from backend.agents.stephanie import StephanieAgent
from backend.agents.gcagent import GCAgent
from backend.agents.permit_stream import PermitStreamAgent
from backend.agents.cyborg import CyborgAgent
from backend.agents.audit_beacon import AuditBeaconAgent

logger = logging.getLogger(__name__)


EVENT_ROUTING: dict[str, AgentFamily] = {
    # Revenue / intake
    "lead_created": AgentFamily.STEPHANIE,
    "lead_updated": AgentFamily.STEPHANIE,
    "estimate_created": AgentFamily.STEPHANIE,
    "estimate_sent": AgentFamily.STEPHANIE,
    "estimate_approved": AgentFamily.STEPHANIE,
    "ops_brief_requested": AgentFamily.STEPHANIE,
    # Construction execution
    "job_activated": AgentFamily.GCAGENT,
    "job_updated": AgentFamily.GCAGENT,
    "daily_log_submitted": AgentFamily.GCAGENT,
    "schedule_changed": AgentFamily.GCAGENT,
    "cost_recorded": AgentFamily.GCAGENT,
    "crew_assigned": AgentFamily.GCAGENT,
    # Permits
    "permit_submitted": AgentFamily.PERMIT_STREAM,
    "permit_status_changed": AgentFamily.PERMIT_STREAM,
    "inspection_scheduled": AgentFamily.PERMIT_STREAM,
    "inspection_completed": AgentFamily.PERMIT_STREAM,
    "zoning_review_requested": AgentFamily.PERMIT_STREAM,
    # Security / governance
    "action_verification_requested": AgentFamily.CYBORG,
    "risk_assessment_requested": AgentFamily.CYBORG,
    "kill_switch_toggled": AgentFamily.CYBORG,
    "authorization_check": AgentFamily.CYBORG,
    # Audit
    "trust_record_created": AgentFamily.AUDIT_BEACON,
    "chain_verification_requested": AgentFamily.AUDIT_BEACON,
    "proof_requested": AgentFamily.AUDIT_BEACON,
}


class AgentMesh:
    """
    The NoblePort OS kernel.

    Holds all five agents, routes events to the correct handler,
    and provides aggregate health telemetry.
    """

    def __init__(self) -> None:
        self.stephanie = StephanieAgent()
        self.gcagent = GCAgent()
        self.permit_stream = PermitStreamAgent()
        self.cyborg = CyborgAgent()
        self.audit_beacon = AuditBeaconAgent()

        self._agents: dict[AgentFamily, BaseAgent] = {
            AgentFamily.STEPHANIE: self.stephanie,
            AgentFamily.GCAGENT: self.gcagent,
            AgentFamily.PERMIT_STREAM: self.permit_stream,
            AgentFamily.CYBORG: self.cyborg,
            AgentFamily.AUDIT_BEACON: self.audit_beacon,
        }

    # -----------------------------------------------------------------
    # Event Routing
    # -----------------------------------------------------------------

    async def route_event(
        self, event_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Route an event to the correct agent based on event type.

        Falls back to Stephanie for unknown events (she's the front door).
        """
        family = EVENT_ROUTING.get(event_type, AgentFamily.STEPHANIE)
        agent = self._agents[family]

        logger.info(
            "Routing event '%s' to %s (%s)",
            event_type, agent.name, family.value,
        )

        result = await agent.execute_task(event_type, payload)

        # Record every event in audit trail
        await self.audit_beacon.execute_task("record_event", {
            "actor": payload.get("actor", "system"),
            "actor_type": payload.get("actor_type", "system"),
            "agent_family": family.value,
            "action": event_type,
            "subject_type": payload.get("subject_type", "event"),
            "subject_id": payload.get("subject_id", ""),
            "detail": payload.get("detail", f"Event: {event_type}"),
            "approval_type": payload.get("approval_type", "auto"),
        })

        return {
            "event_type": event_type,
            "routed_to": family.value,
            "agent": agent.name,
            "result": result.result if result.success else {"error": result.error},
            "success": result.success,
        }

    # -----------------------------------------------------------------
    # System Health
    # -----------------------------------------------------------------

    async def get_system_health(self) -> dict[str, Any]:
        """Aggregated health check across all agents."""
        agent_health = {}
        for family, agent in self._agents.items():
            telemetry = await agent.health_check()
            agent_health[family.value] = {
                "name": telemetry.name,
                "health": telemetry.health.value,
                "status": telemetry.status.value,
                "queue_depth": telemetry.queue_depth,
                "in_flight": telemetry.in_flight,
                "p95_latency_ms": telemetry.p95_latency_ms,
                "error_rate": telemetry.error_rate,
                "uptime_30d": telemetry.uptime_30d,
                "last_heartbeat": telemetry.last_heartbeat,
                "total_tasks": telemetry.total_tasks_completed,
            }

        # Overall health
        healths = [
            AgentHealth(v["health"]) for v in agent_health.values()
        ]
        if any(h == AgentHealth.UNHEALTHY for h in healths):
            overall = "unhealthy"
        elif any(h == AgentHealth.DEGRADED for h in healths):
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "overall_health": overall,
            "agent_count": len(self._agents),
            "agents": agent_health,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_agent_mesh_summary(self) -> dict[str, Any]:
        """
        Summary stats matching the frontend AgentMeshSummary type.
        """
        total = len(self._agents)
        healthy = 0
        degraded = 0
        unhealthy = 0
        total_queue = 0
        total_in_flight = 0
        top_latency = 0.0

        for agent in self._agents.values():
            telemetry = await agent.health_check()
            if telemetry.health == AgentHealth.HEALTHY:
                healthy += 1
            elif telemetry.health == AgentHealth.DEGRADED:
                degraded += 1
            else:
                unhealthy += 1

            total_queue += telemetry.queue_depth
            total_in_flight += telemetry.in_flight
            top_latency = max(top_latency, telemetry.p95_latency_ms)

        return {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "totalQueue": total_queue,
            "totalInFlight": total_in_flight,
            "topLatencyMs": round(top_latency, 2),
        }

    # -----------------------------------------------------------------
    # Agent Access
    # -----------------------------------------------------------------

    def get_agent(self, family: AgentFamily) -> BaseAgent:
        """Get a specific agent by family."""
        return self._agents[family]

    async def broadcast(
        self, event_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Broadcast an event to all agents."""
        results = {}
        for family, agent in self._agents.items():
            try:
                result = await agent.execute_task(event_type, payload)
                results[family.value] = {
                    "success": result.success,
                    "result": result.result,
                }
            except Exception as exc:
                results[family.value] = {
                    "success": False,
                    "error": str(exc),
                }
        return results


def create_agent_mesh() -> AgentMesh:
    """Factory function for the agent mesh."""
    return AgentMesh()
