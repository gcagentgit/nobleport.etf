"""
Tests for the systems truth registry.

The hard guarantees: VERIFIED is impossible without a named verifier
(fail-closed), repo code-completeness earns STAGED and never VERIFIED,
external claims are classified by their own evidence (EpochX = CLAIMED,
avatar fleet = DEMO), regulated layers sit on LEGAL_HOLD with mandatory
human approval, and the rollups reconcile.
"""

from __future__ import annotations

import pytest

from backend.systems import (
    BUCKET_DEFINITIONS,
    PROMOTION_GATES,
    SystemNode,
    TruthBucket,
    build_registry,
    nodes_from_program,
)


def test_every_bucket_has_definition_and_gate():
    for bucket in TruthBucket:
        assert bucket in BUCKET_DEFINITIONS
        assert bucket in PROMOTION_GATES


def test_verified_requires_named_verifier():
    with pytest.raises(ValueError, match="fail-closed"):
        SystemNode(
            key="fake", name="Fake", category="Test",
            bucket=TruthBucket.VERIFIED, summary="", evidence=(),
            next_gate="", source="declared:test",
        )


def test_verifier_forbidden_on_unverified_nodes():
    with pytest.raises(ValueError, match="only valid on VERIFIED"):
        SystemNode(
            key="fake", name="Fake", category="Test",
            bucket=TruthBucket.STAGED, summary="", evidence=(),
            next_gate="", source="declared:test", verified_by="someone",
        )


def test_repo_code_complete_is_staged_never_verified():
    nodes = nodes_from_program()
    assert nodes, "program bridge produced no nodes"
    for n in nodes:
        assert n.bucket in {TruthBucket.STAGED, TruthBucket.PLANNED}
        assert n.bucket is not TruthBucket.VERIFIED
        assert n.source == "measured:repo"


def test_registry_has_zero_verified_systems():
    """The honest baseline: nothing is independently verified live yet."""
    registry = build_registry()
    assert registry.verified_count == 0
    payload = registry.to_dict()
    assert "0 of" in payload["hard_truth"]


def test_external_claims_classified_by_their_own_evidence():
    nodes = {n.key: n for n in build_registry().nodes}
    assert nodes["epochx_mesh"].bucket is TruthBucket.CLAIMED
    assert nodes["avatar_fleet"].bucket is TruthBucket.DEMO
    assert nodes["truth_inventory_workbook"].bucket is TruthBucket.REFERENCE


def test_regulated_layers_are_held_and_human_gated():
    nodes = {n.key: n for n in build_registry().nodes}
    token = nodes["nbpt_token_issuance"]
    assert token.bucket is TruthBucket.LEGAL_HOLD
    assert token.human_approval_required is True
    trading = nodes["trading_live_execution"]
    assert trading.bucket is TruthBucket.BLOCKED
    assert trading.human_approval_required is True


def test_no_duplicate_keys_and_rollup_reconciles():
    registry = build_registry()
    keys = [n.key for n in registry.nodes]
    assert len(keys) == len(set(keys))
    assert sum(registry.by_bucket().values()) == len(registry.nodes)


def test_execution_path_references_real_nodes():
    registry = build_registry()
    keys = {n.key for n in registry.nodes}
    payload = registry.to_dict()
    for step in payload["execution_path"]:
        assert step["node"] in keys, f"execution path references unknown node {step['node']}"
