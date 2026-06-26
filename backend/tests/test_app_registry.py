"""
Tests for the NoblePort Application Registry.

These assert that the inventory of external builds stays honest: the verified
Base44 count is pinned, copies and concepts are never silently promoted to
"exists", and the named-but-absent core products are recorded as such with the
"absence in Base44 is not absence everywhere" distinction intact.
"""

from __future__ import annotations

import pytest

from backend.core.app_registry import (
    APP_REGISTRY,
    BASE44_APPS,
    CORE_PRODUCTS,
    AppRecord,
    ApplicationRegistry,
    Platform,
    TruthStatus,
    UNVERIFIED,
)


def test_registry_validates():
    # The singleton validates at import; re-running must stay clean.
    APP_REGISTRY.validate()


def test_base44_count_is_pinned_at_21():
    # Verified from Base44 list_user_apps on 2026-06-26. If this moves, the
    # workspace genuinely changed and the registry must be re-read, not nudged.
    assert len(BASE44_APPS) == 21
    assert len(APP_REGISTRY.base44_apps()) == 21


def test_base44_ids_are_unique():
    ids = [a.platform_id for a in APP_REGISTRY.base44_apps()]
    assert len(ids) == len(set(ids))


def test_only_one_clearly_named_core_base44_app():
    # "Nobleport Nexus" is the sole clearly-named NoblePort-core Base44 app;
    # its (Copy) is a duplicate, not a second product.
    nexus = [a for a in APP_REGISTRY.base44_apps() if a.name.startswith("Nobleport Nexus")]
    assert len(nexus) == 2
    originals = [a for a in nexus if a.truth_status is not TruthStatus.DUPLICATE]
    assert len(originals) == 1
    assert originals[0].platform_id == "68ace5b69c57f0a42e92246f"


def test_every_duplicate_names_its_original():
    for app in APP_REGISTRY.by_status(TruthStatus.DUPLICATE):
        assert app.duplicate_of, f"{app.name} missing duplicate_of"


def test_crypto_apps_exist_only_as_copies():
    # Both Crypto apps are present only as (Copy); no originals in the workspace.
    crypto = [a for a in BASE44_APPS if "Crypto" in a.name]
    assert crypto, "expected Crypto apps in the workspace"
    assert all(a.truth_status is TruthStatus.DUPLICATE for a in crypto)


def test_core_products_in_repo_are_verified_not_in_base44():
    in_repo = {a.name: a for a in CORE_PRODUCTS if a.platform is Platform.REPO}
    for name in ("Stephanie.ai", "GCagent.ai", "PermitStream.ai", "NoblePort Payment Node"):
        assert name in in_repo
        assert in_repo[name].truth_status is TruthStatus.VERIFIED_EXISTS
        assert in_repo[name].repository == "gcagent/nobleport.etf"
        # Present as code here, but absent from the Base44 workspace.
        assert in_repo[name].platform is not Platform.BASE44


def test_unfound_core_products_are_named_absent():
    absent = {a.name: a for a in CORE_PRODUCTS if a.truth_status is TruthStatus.NAMED_ABSENT}
    for name in ("Kuzo.io", "NobleWatch-pro"):
        assert name in absent
        assert absent[name].platform is Platform.UNKNOWN
        assert absent[name].platform_id is None


def test_unverifiable_columns_are_marked_not_guessed():
    # Base44 exposes name + id only. URL / environment / production evidence
    # must be the explicit UNVERIFIED sentinel, never a fabricated value.
    for app in APP_REGISTRY.base44_apps():
        assert app.url == UNVERIFIED
        assert app.environment == UNVERIFIED
        assert app.production_evidence == UNVERIFIED


def test_named_absent_rejects_a_platform_id():
    bad = ApplicationRegistry(
        apps=(
            AppRecord(
                name="Phantom",
                truth_status=TruthStatus.NAMED_ABSENT,
                platform=Platform.UNKNOWN,
                platform_id="should-not-be-here",
            ),
        )
    )
    with pytest.raises(ValueError):
        bad.validate()


def test_summary_counts_are_consistent():
    s = APP_REGISTRY.summary()
    assert s["base44Total"] == 21
    assert s["totalRows"] == len(BASE44_APPS) + len(CORE_PRODUCTS)
    assert sum(s["byTruthStatus"].values()) == s["totalRows"]
