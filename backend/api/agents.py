"""
Agent Mesh API — Agent Registry & Health Monitoring

Manages the AI agent mesh: registration, health reporting,
task assignment, and kill-switch control. Supports the
Stephanie.ai orchestration layer and Cyborg.ai compliance.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.agent_registry import (
    AgentFamily,
    AgentHealth,
    RegisteredAgent,
)
from backend.services.audit_beacon import AuditBeacon
from backend.models.audit_entry import AuditAction, ApprovalType

router = APIRouter()


class AgentRegister(BaseModel):
    name: str
    family: str
    role: str
    version: str = "1.0.0"
    capabilities_json: str | None = None


class AgentHeartbeat(BaseModel):
    health: str
    queue_depth: int = 0
    in_flight: int = 0
    p95_latency_ms: float = 0.0
    error_rate: float = 0.0
    current_task: str | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    family: str
    role: str
    version: str
    health: str
    queue_depth: int
    in_flight: int
    p95_latency_ms: float
    error_rate: float
    uptime_30d: float
    tasks_completed: int
    last_heartbeat: str | None
    kill_switch_armed: bool
    current_task: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class KillSwitchRequest(BaseModel):
    armed: bool
    scope: str | None = None


@router.get("")
async def list_agents(
    family: str | None = None,
    health: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(RegisteredAgent)
    if family:
        query = query.where(RegisteredAgent.family == AgentFamily(family))
    if health:
        query = query.where(RegisteredAgent.health == AgentHealth(health))

    result = await db.execute(query.order_by(RegisteredAgent.name))
    agents = result.scalars().all()

    return {
        "items": [AgentResponse.model_validate(a) for a in agents],
        "total": len(agents),
    }


@router.post("", response_model=AgentResponse)
async def register_agent(
    data: AgentRegister, db: AsyncSession = Depends(get_db)
):
    agent = RegisteredAgent(
        name=data.name,
        family=AgentFamily(data.family),
        role=data.role,
        version=data.version,
        health=AgentHealth.UNKNOWN,
        capabilities_json=data.capabilities_json,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    await AuditBeacon.record(
        db, operator="system", action=AuditAction.CREATE,
        subject_type="agent", subject_id=agent.id,
        subject_label=agent.name,
        detail=f"Registered agent {agent.name} [{data.family}]",
    )

    return AgentResponse.model_validate(agent)


@router.post("/{agent_id}/heartbeat", response_model=AgentResponse)
async def agent_heartbeat(
    agent_id: str,
    data: AgentHeartbeat,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RegisteredAgent).where(RegisteredAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.health = AgentHealth(data.health)
    agent.queue_depth = data.queue_depth
    agent.in_flight = data.in_flight
    agent.p95_latency_ms = data.p95_latency_ms
    agent.error_rate = data.error_rate
    agent.current_task = data.current_task
    agent.last_heartbeat = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.post("/{agent_id}/kill-switch")
async def toggle_kill_switch(
    agent_id: str,
    data: KillSwitchRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RegisteredAgent).where(RegisteredAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.kill_switch_armed = data.armed
    agent.kill_switch_scope = data.scope

    await db.commit()

    await AuditBeacon.record(
        db, operator="operator", action=AuditAction.KILL_SWITCH,
        subject_type="agent", subject_id=agent.id,
        subject_label=agent.name,
        approval=ApprovalType.HUMAN,
        detail=f"Kill-switch {'ARMED' if data.armed else 'DISARMED'} scope={data.scope}",
    )

    return {
        "agent_id": agent.id,
        "name": agent.name,
        "kill_switch_armed": agent.kill_switch_armed,
        "scope": agent.kill_switch_scope,
    }


@router.get("/mesh/summary")
async def mesh_summary(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count()).select_from(RegisteredAgent))
    healthy = await db.execute(
        select(func.count()).select_from(RegisteredAgent)
        .where(RegisteredAgent.health == AgentHealth.HEALTHY)
    )
    degraded = await db.execute(
        select(func.count()).select_from(RegisteredAgent)
        .where(RegisteredAgent.health == AgentHealth.DEGRADED)
    )
    unhealthy = await db.execute(
        select(func.count()).select_from(RegisteredAgent)
        .where(RegisteredAgent.health == AgentHealth.UNHEALTHY)
    )
    total_queue = await db.execute(
        select(func.coalesce(func.sum(RegisteredAgent.queue_depth), 0))
        .select_from(RegisteredAgent)
    )
    total_in_flight = await db.execute(
        select(func.coalesce(func.sum(RegisteredAgent.in_flight), 0))
        .select_from(RegisteredAgent)
    )
    top_latency = await db.execute(
        select(func.coalesce(func.max(RegisteredAgent.p95_latency_ms), 0))
        .select_from(RegisteredAgent)
    )

    return {
        "total": total.scalar() or 0,
        "healthy": healthy.scalar() or 0,
        "degraded": degraded.scalar() or 0,
        "unhealthy": unhealthy.scalar() or 0,
        "totalQueue": int(total_queue.scalar() or 0),
        "totalInFlight": int(total_in_flight.scalar() or 0),
        "topLatencyMs": float(top_latency.scalar() or 0),
    }
