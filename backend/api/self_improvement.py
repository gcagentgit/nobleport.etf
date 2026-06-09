"""
NoblePort Stephanie Self-Improvement API

Surfaces the recursive self-improvement loop for Mission Control:

  GET  /policy        current tuned policy + generation
  GET  /state         full loop state (policy, breaker, pending proposals)
  GET  /history       the recursive chain of policy generations
  GET  /proposals     proposals awaiting human approval
  POST /cycle         run one improvement cycle (dry-run unless apply=true)
  POST /proposals/{id}/approve
  POST /proposals/{id}/reject
  POST /rollback      restore a prior generation
  POST /breaker/reset clear an open circuit breaker

Governed, high-impact actions (approve / reject / rollback / breaker reset)
are written to the AuditBeacon hash chain so the whole self-improvement
history is independently verifiable.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Request

from backend.agents.self_improvement import ControlMode, RecursiveSelfImprovementEngine
from backend.agents.truth_registry import CONTROL_RULE, registry_snapshot

router = APIRouter()


def _engine(request: Request) -> RecursiveSelfImprovementEngine:
    """Resolve Stephanie's self-improvement engine from the live agent mesh."""
    mesh = getattr(request.app.state, "agent_mesh", None)
    if mesh is None:
        raise HTTPException(status_code=503, detail="Agent mesh not initialized")
    return mesh.stephanie.self_improvement


async def _audit(request: Request, action: str, detail: dict[str, Any], actor: str) -> None:
    """Record a governed self-improvement action to the AuditBeacon chain."""
    mesh = getattr(request.app.state, "agent_mesh", None)
    if mesh is None:
        return
    await mesh.audit_beacon.execute_task("record_event", {
        "actor": actor,
        "actor_type": "human",
        "agent_family": "Stephanie",
        "action": f"self_improvement.{action}",
        "subject_type": "policy",
        "subject_id": str(detail.get("generation", "")),
        "detail": detail,
        "approval_type": "human",
    })


@router.get("/control-rule")
async def get_control_rule(request: Request) -> dict[str, Any]:
    """
    The operating model: AI observes -> drafts -> scores -> recommends ->
    human approves -> system logs -> system learns. Surfaces the live control
    mode so the UI can show whether the loop is fail-closed (human-gated).
    """
    engine = _engine(request)
    return {
        "control_rule": CONTROL_RULE,
        "control_mode": engine.control_mode.value,
        "fail_closed": engine.control_mode == ControlMode.FAIL_CLOSED,
    }


@router.get("/truth")
async def get_truth_registry() -> dict[str, Any]:
    """The honest truth layer — component statuses, flywheels, priority phases."""
    return registry_snapshot()


@router.get("/policy")
async def get_policy(request: Request) -> dict[str, Any]:
    """Current tuned decision policy and generation number."""
    engine = _engine(request)
    return {
        "generation": engine.generation,
        "control_mode": engine.control_mode.value,
        "policy": engine.current.model_dump(),
        "objective_score": engine.score(engine.current) if engine.outcomes else None,
    }


@router.get("/state")
async def get_state(request: Request) -> dict[str, Any]:
    """Full loop state — policy, circuit breaker, pending proposals, window."""
    return _engine(request).state()


@router.get("/history")
async def get_history(request: Request) -> dict[str, Any]:
    """The recursive chain of applied policy generations."""
    engine = _engine(request)
    return {
        "generation": engine.generation,
        "versions": [v.model_dump() for v in engine.history],
    }


@router.get("/proposals")
async def list_proposals(request: Request) -> dict[str, Any]:
    """Proposals awaiting human approval."""
    engine = _engine(request)
    return {"pending": [p.model_dump() for p in engine.pending.values()]}


@router.post("/cycle")
async def run_cycle(
    request: Request,
    auto_apply: bool = Query(False, description="Commit auto-eligible (LOW-risk) changes."),
    lookback_days: int = Query(180, ge=1, le=1095),
) -> dict[str, Any]:
    """
    Run one recursive self-improvement cycle against real lead outcomes.

    Dry-run by default: produces a governed proposal. With ``auto_apply``,
    only LOW-risk, improvement-proven changes (breaker closed) are committed;
    MEDIUM/HIGH-risk changes are always queued for human approval.
    """
    mesh = getattr(request.app.state, "agent_mesh", None)
    if mesh is None:
        raise HTTPException(status_code=503, detail="Agent mesh not initialized")
    result = await mesh.stephanie.run_self_improvement(
        auto_apply=auto_apply, lookback_days=lookback_days,
    )
    report = result.get("report", {})
    if report.get("applied"):
        await _audit(request, "cycle_auto_applied", {
            "generation": report.get("generation"),
            "proposal": report.get("proposal"),
        }, actor="stephanie-auto")
    return result


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    request: Request,
    proposal_id: str,
    approved_by: str = Body("operator", embed=True),
) -> dict[str, Any]:
    """Approve and apply a pending proposal as the next generation."""
    engine = _engine(request)
    try:
        version = engine.approve(proposal_id, approved_by=approved_by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await _audit(request, "approve", {
        "generation": version.generation,
        "changes": version.policy.model_dump(),
        "approved_by": approved_by,
    }, actor=approved_by)
    return {"applied": True, "version": version.model_dump()}


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(
    request: Request,
    proposal_id: str,
    rejected_by: str = Body("operator", embed=True),
    reason: str = Body("", embed=True),
) -> dict[str, Any]:
    """Reject a pending proposal."""
    engine = _engine(request)
    try:
        engine.reject(proposal_id, rejected_by=rejected_by, reason=reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await _audit(request, "reject", {
        "proposal_id": proposal_id, "rejected_by": rejected_by, "reason": reason,
    }, actor=rejected_by)
    return {"rejected": True, "proposal_id": proposal_id}


@router.post("/rollback")
async def rollback(
    request: Request,
    generation: int = Body(..., embed=True),
    actor: str = Body("operator", embed=True),
) -> dict[str, Any]:
    """Restore a prior generation's policy (recorded as a new version)."""
    engine = _engine(request)
    try:
        version = engine.rollback(generation, actor=actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await _audit(request, "rollback", {
        "restored_generation": generation, "new_generation": version.generation, "actor": actor,
    }, actor=actor)
    return {"rolled_back_to": generation, "version": version.model_dump()}


@router.post("/verify")
async def verify(
    request: Request,
    actor: str = Body("operator", embed=True),
) -> dict[str, Any]:
    """
    Monitor -> Lock / Rollback. Prove the provisional in-force generation
    still beats its parent on the latest outcomes: lock it if it holds,
    auto-roll back if it regressed.
    """
    engine = _engine(request)
    report = engine.verify()
    await _audit(request, "verify", {
        "generation": report.generation,
        "held_up": report.held_up,
        "locked": report.locked,
        "rolled_back_to": report.rolled_back_to,
    }, actor=actor)
    return report.model_dump()


@router.post("/control-mode")
async def set_control_mode(
    request: Request,
    mode: str = Body(..., embed=True, description="fail_closed | operational_auto"),
    actor: str = Body("operator", embed=True),
) -> dict[str, Any]:
    """
    Switch the control mode. FAIL_CLOSED (default) keeps every change
    human-gated; OPERATIONAL_AUTO is an explicit, audited opt-in that lets
    LOW-risk operational tuning auto-apply. Recorded on the audit chain.
    """
    engine = _engine(request)
    try:
        engine.control_mode = ControlMode(mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown control mode: {mode}") from exc
    await _audit(request, "control_mode_change", {
        "mode": engine.control_mode.value, "actor": actor, "generation": engine.generation,
    }, actor=actor)
    return {"control_mode": engine.control_mode.value}


@router.post("/breaker/reset")
async def reset_breaker(
    request: Request,
    actor: str = Body("operator", embed=True),
) -> dict[str, Any]:
    """Manually clear an open circuit breaker to re-enable auto-apply."""
    engine = _engine(request)
    engine.breaker.reset()
    await _audit(request, "breaker_reset", {"actor": actor, "generation": engine.generation}, actor=actor)
    return {"breaker": engine.breaker.model_dump()}
