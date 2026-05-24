"""
AuditBeacon — Immutable Operational Memory

Hash-chained event ledger that records every significant action in the
NoblePort OS. Each record contains:
  - Who acted
  - What changed
  - What approved it
  - What document supports it
  - What payment occurred
  - What AI suggested
  - Whether a human approved

This is the foundation of NoblePort Proof of Trust.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from backend.agents.base import AgentFamily, BaseAgent

logger = logging.getLogger(__name__)


class AuditBeaconAgent(BaseAgent):

    def __init__(self) -> None:
        super().__init__(
            name="AuditBeacon",
            family=AgentFamily.AUDIT_BEACON,
            role="Immutable operational memory (hash-chain ledger)",
            agent_id="audit-beacon-primary",
        )
        self._chain: list[dict[str, Any]] = []
        self._last_hash: str = "0" * 64  # genesis hash

    async def _handle_task(
        self, task_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        handlers = {
            "record_event": self.record_event,
            "get_audit_trail": self.get_audit_trail,
            "verify_chain_integrity": self.verify_chain_integrity,
            "get_proof_of_trust": self.get_proof_of_trust,
            "get_chain_stats": self.get_chain_stats,
        }
        handler = handlers.get(task_type)
        if not handler:
            raise ValueError(f"Unknown AuditBeacon task: {task_type}")
        return await handler(payload)

    # -----------------------------------------------------------------
    # Hash Chain
    # -----------------------------------------------------------------

    def _compute_hash(
        self,
        prev_hash: str,
        actor: str,
        action: str,
        subject: str,
        timestamp: str,
    ) -> str:
        data = f"{prev_hash}|{actor}|{action}|{subject}|{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    # -----------------------------------------------------------------
    # Record Event
    # -----------------------------------------------------------------

    async def record_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Record an event in the hash-chained audit ledger.

        Every record captures:
          - actor / actor_type / agent_family
          - action performed
          - subject (entity acted upon)
          - approval_type and approved_by
          - document_ref and document_hash
          - payment_id and payment_amount
          - ai_suggested, ai_suggestion, ai_confidence
          - human_overrode_ai
        """
        now = datetime.now(timezone.utc)
        ts = now.isoformat()

        actor = payload.get("actor", "system")
        action = payload.get("action", "unknown")
        subject_type = payload.get("subject_type", "unknown")
        subject_id = payload.get("subject_id", "")
        subject = f"{subject_type}:{subject_id}"

        record_hash = self._compute_hash(
            self._last_hash, actor, action, subject, ts
        )

        record = {
            "id": f"trust-{len(self._chain) + 1:06d}",
            "ts": ts,
            "actor": actor,
            "actor_type": payload.get("actor_type", "system"),
            "agent_family": payload.get("agent_family"),
            "action": action,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "detail": payload.get("detail", ""),
            "approval_type": payload.get("approval_type", "none"),
            "approved_by": payload.get("approved_by"),
            "approval_reason": payload.get("approval_reason"),
            "ai_suggested": payload.get("ai_suggested", False),
            "ai_suggestion": payload.get("ai_suggestion"),
            "ai_confidence": payload.get("ai_confidence"),
            "human_overrode_ai": payload.get("human_overrode_ai", False),
            "document_ref": payload.get("document_ref"),
            "document_hash": payload.get("document_hash"),
            "payment_id": payload.get("payment_id"),
            "payment_amount": payload.get("payment_amount"),
            "record_hash": record_hash,
            "prev_hash": self._last_hash,
            "status": "committed",
        }

        self._chain.append(record)
        self._last_hash = record_hash

        logger.info(
            "AuditBeacon: recorded %s by %s on %s (chain length: %d)",
            action, actor, subject, len(self._chain),
        )

        return {
            "record_id": record["id"],
            "record_hash": record_hash,
            "chain_position": len(self._chain),
            "status": "committed",
        }

    # -----------------------------------------------------------------
    # Audit Trail
    # -----------------------------------------------------------------

    async def get_audit_trail(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get the full audit trail for a subject."""
        subject_id = payload.get("subject_id", "")
        subject_type = payload.get("subject_type")

        trail = [
            r for r in self._chain
            if r["subject_id"] == subject_id
            and (subject_type is None or r["subject_type"] == subject_type)
        ]

        return {
            "subject_id": subject_id,
            "subject_type": subject_type,
            "record_count": len(trail),
            "records": trail,
        }

    # -----------------------------------------------------------------
    # Chain Integrity Verification
    # -----------------------------------------------------------------

    async def verify_chain_integrity(
        self, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Verify the integrity of the entire hash chain."""
        if not self._chain:
            return {"valid": True, "chain_length": 0, "errors": []}

        errors = []
        expected_prev = "0" * 64

        for i, record in enumerate(self._chain):
            if record["prev_hash"] != expected_prev:
                errors.append({
                    "position": i,
                    "record_id": record["id"],
                    "error": "prev_hash mismatch",
                    "expected": expected_prev,
                    "actual": record["prev_hash"],
                })

            recomputed = self._compute_hash(
                record["prev_hash"],
                record["actor"],
                record["action"],
                f"{record['subject_type']}:{record['subject_id']}",
                record["ts"],
            )

            if record["record_hash"] != recomputed:
                errors.append({
                    "position": i,
                    "record_id": record["id"],
                    "error": "record_hash tampered",
                    "expected": recomputed,
                    "actual": record["record_hash"],
                })

            expected_prev = record["record_hash"]

        return {
            "valid": len(errors) == 0,
            "chain_length": len(self._chain),
            "errors": errors,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------
    # Proof of Trust
    # -----------------------------------------------------------------

    async def get_proof_of_trust(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Get complete proof of trust for a specific record.

        Returns the record itself plus chain context:
          - Chain position
          - Hash linkage (prev/next)
          - Whether the record is verified
        """
        record_id = payload.get("record_id", "")

        record = None
        position = -1
        for i, r in enumerate(self._chain):
            if r["id"] == record_id:
                record = r
                position = i
                break

        if record is None:
            return {"found": False, "record_id": record_id}

        # Verify this specific record
        recomputed = self._compute_hash(
            record["prev_hash"],
            record["actor"],
            record["action"],
            f"{record['subject_type']}:{record['subject_id']}",
            record["ts"],
        )
        hash_valid = record["record_hash"] == recomputed

        next_hash = (
            self._chain[position + 1]["prev_hash"]
            if position + 1 < len(self._chain)
            else None
        )
        chain_linked = next_hash == record["record_hash"] if next_hash else True

        return {
            "found": True,
            "record": record,
            "chain_context": {
                "position": position,
                "chain_length": len(self._chain),
                "hash_valid": hash_valid,
                "chain_linked": chain_linked,
                "prev_hash": record["prev_hash"],
                "next_links_to_this": chain_linked,
            },
            "trust_proof": {
                "who_acted": record["actor"],
                "actor_type": record["actor_type"],
                "what_changed": record["action"],
                "what_approved_it": record["approval_type"],
                "approved_by": record["approved_by"],
                "what_document": record["document_ref"],
                "what_payment": record["payment_id"],
                "payment_amount": record["payment_amount"],
                "ai_suggested": record["ai_suggested"],
                "ai_confidence": record["ai_confidence"],
                "human_approved": record["approval_type"] == "human",
                "human_overrode_ai": record["human_overrode_ai"],
                "integrity_verified": hash_valid and chain_linked,
            },
        }

    # -----------------------------------------------------------------
    # Chain Stats
    # -----------------------------------------------------------------

    async def get_chain_stats(
        self, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Chain-wide statistics."""
        if not self._chain:
            return {"chain_length": 0, "stats": {}}

        actor_types = {}
        approval_types = {}
        ai_suggested_count = 0
        human_override_count = 0

        for r in self._chain:
            at = r.get("actor_type", "unknown")
            actor_types[at] = actor_types.get(at, 0) + 1

            ap = r.get("approval_type", "none")
            approval_types[ap] = approval_types.get(ap, 0) + 1

            if r.get("ai_suggested"):
                ai_suggested_count += 1
            if r.get("human_overrode_ai"):
                human_override_count += 1

        return {
            "chain_length": len(self._chain),
            "actor_types": actor_types,
            "approval_types": approval_types,
            "ai_suggested_count": ai_suggested_count,
            "human_override_count": human_override_count,
            "first_record": self._chain[0]["ts"],
            "last_record": self._chain[-1]["ts"],
            "last_hash": self._last_hash,
        }
