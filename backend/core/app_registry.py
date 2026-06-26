"""
NoblePort Application Registry — Canonical Inventory of External Builds

This module is the single, authoritative, machine-readable answer to a
deceptively hard question: *which applications actually exist, where do they
live, and which of them are real?*

It exists to stop three different kinds of thing from being counted as if they
were the same:

  1. **Live systems** — code that runs and does work (e.g. the agents in
     ``backend/agents`` that front Stephanie.ai, GCagent, and PermitStream).
  2. **Concepts** — products named in strategy/NP-OS docs that do not yet
     have a verified implementation anywhere (e.g. Kuzo.io, NobleWatch-pro).
  3. **Copies & experiments** — duplicate builds and throwaway templates
     sitting in a builder workspace (e.g. the many Base44 ``(Copy)`` apps).

Every row carries an explicit :class:`TruthStatus`. Nothing is promoted from
"this name was mentioned" to "this exists" without a cited source. Columns we
cannot verify from an authoritative source are recorded as the literal
``UNVERIFIED`` sentinel rather than guessed — an empty-looking honest cell is
worth more than a confident wrong one.

Provenance for the Base44 rows: the 21 Base44 apps below were read directly
from the Base44 API (``list_user_apps``) on 2026-06-26. Base44 IDs — not names,
which duplicate freely — are the stable keys. The Base44 API exposes name and
id only; URL, deployment, environment, and production evidence are NOT
derivable from it and are therefore marked ``UNVERIFIED`` pending a manual
check against the builder console / hosting provider.

This file is authoritative and self-validating (``APP_REGISTRY.validate()``
runs at import). Its human-readable companion is
``docs/np-os/application-registry.md`` and the two must stay in lockstep.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


UNVERIFIED = "UNVERIFIED"


class Platform(str, Enum):
    """Where a build physically lives."""

    BASE44 = "base44"
    REPO = "repo"          # code in this git repository (gcagent/nobleport.etf)
    REPLIT = "replit"
    MANUS = "manus"
    UNKNOWN = "unknown"


class TruthStatus(str, Enum):
    """How sure we are that an app is real, and what kind of real.

    The whole point of the registry is that these are NOT interchangeable.
    """

    # Existence proven by an authoritative source (Base44 API listing, or code
    # present in this repo). NOTE: this proves existence, NOT that the app is
    # deployed, reachable, or in production.
    VERIFIED_EXISTS = "verified_exists"

    # A name-copy of another registered app (Base44 "(Copy)"). Real bytes, but
    # not an independent system — must not be counted as a distinct product.
    DUPLICATE = "duplicate"

    # Present in a workspace but judged to be a template / experiment / build
    # unrelated to the NoblePort ecosystem.
    EXPERIMENT = "experiment"

    # Referenced by name in NoblePort strategy/NP-OS docs but NOT found in any
    # verified source. A concept until proven otherwise.
    NAMED_ABSENT = "named_absent"

    # Existence asserted somewhere but not yet checked against any source.
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class AppRecord:
    """One application, one row, one truth status.

    Fields mirror the registry columns requested for the inventory: name,
    owner, repository, platform location, URL, purpose, environment,
    integration dependencies, production evidence, and truth status.
    """

    name: str
    truth_status: TruthStatus
    platform: Platform
    # Stable platform-native identifier (Base44 id, repo path, etc.).
    platform_id: str | None = None
    owner: str = UNVERIFIED
    repository: str = UNVERIFIED
    url: str = UNVERIFIED
    purpose: str = UNVERIFIED
    environment: str = UNVERIFIED
    integration_dependencies: tuple[str, ...] = ()
    production_evidence: str = UNVERIFIED
    # For DUPLICATE rows: the name of the app this is a copy of.
    duplicate_of: str | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "truthStatus": self.truth_status.value,
            "platform": self.platform.value,
            "platformId": self.platform_id,
            "owner": self.owner,
            "repository": self.repository,
            "url": self.url,
            "purpose": self.purpose,
            "environment": self.environment,
            "integrationDependencies": list(self.integration_dependencies),
            "productionEvidence": self.production_evidence,
            "duplicateOf": self.duplicate_of,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Base44 workspace — verified from list_user_apps on 2026-06-26 (21 apps).
# IDs are the stable keys. Names duplicate; ids do not.
# ---------------------------------------------------------------------------

_BASE44_VERIFIED_SOURCE = "Base44 list_user_apps API, read 2026-06-26"

BASE44_APPS: tuple[AppRecord, ...] = (
    # --- NoblePort-core (clearly named) -----------------------------------
    AppRecord(
        name="Nobleport Nexus",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.BASE44,
        platform_id="68ace5b69c57f0a42e92246f",
        purpose="Only clearly-named NoblePort-core app in the Base44 workspace.",
        production_evidence=UNVERIFIED,
        notes=f"Existence verified via {_BASE44_VERIFIED_SOURCE}. Deployment/URL unverified.",
    ),
    AppRecord(
        name="Nobleport Nexus (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68bb29aad4e60929fceffad6",
        duplicate_of="Nobleport Nexus",
        notes=f"Name-copy. Verified present via {_BASE44_VERIFIED_SOURCE}.",
    ),
    # --- Plausibly Web3 / AI related --------------------------------------
    AppRecord(
        name="ENS Identity Lens",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.BASE44,
        platform_id="68aa083c32ee5b441e4b0e12",
        purpose=UNVERIFIED,
        notes=f"Likely Web3/identity. Verified present via {_BASE44_VERIFIED_SOURCE}.",
    ),
    AppRecord(
        name="Stellaris Assets",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.BASE44,
        platform_id="68aa191b21654352ac53348f",
        purpose=UNVERIFIED,
        notes=f"Original of two copies. Verified present via {_BASE44_VERIFIED_SOURCE}.",
    ),
    AppRecord(
        name="Stellaris Assets (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68aa299ffbd2256c2556f9b7",
        duplicate_of="Stellaris Assets",
        notes=f"Name-copy #1. Verified present via {_BASE44_VERIFIED_SOURCE}.",
    ),
    AppRecord(
        name="Stellaris Assets (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68aa2991e01040cd71a387aa",
        duplicate_of="Stellaris Assets",
        notes=f"Name-copy #2. Verified present via {_BASE44_VERIFIED_SOURCE}.",
    ),
    AppRecord(
        name="CryptoPulse AI (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68ab857a69e17e178f1971b0",
        duplicate_of="CryptoPulse AI",
        notes=(
            "Only a (Copy) exists in the workspace; no original 'CryptoPulse AI' "
            f"is present. Verified via {_BASE44_VERIFIED_SOURCE}."
        ),
    ),
    AppRecord(
        name="CryptoChart AI (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68ab85dd565d5e8cc50800f1",
        duplicate_of="CryptoChart AI",
        notes=(
            "Only a (Copy) exists in the workspace; no original 'CryptoChart AI' "
            f"is present. Verified via {_BASE44_VERIFIED_SOURCE}."
        ),
    ),
    # --- Likely experiments / templates / unrelated -----------------------
    AppRecord(
        name="AquaHut",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="68a9fd15179e8fd07373ef5b",
        notes=f"Most-duplicated build (3 copies). Verified via {_BASE44_VERIFIED_SOURCE}.",
    ),
    AppRecord(
        name="AquaHut (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68d67e7711c551c2152abd14",
        duplicate_of="AquaHut",
    ),
    AppRecord(
        name="AquaHut (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68aa045bc9793caf6c241f5f",
        duplicate_of="AquaHut",
    ),
    AppRecord(
        name="AquaHut (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68aa08abbf77d9233404f89a",
        duplicate_of="AquaHut",
    ),
    AppRecord(
        name="HydroTracker",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="68a9d7142597cfe16d0d45f8",
    ),
    AppRecord(
        name="HydroTracker (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68e1b97a4a98c2175cae7130",
        duplicate_of="HydroTracker",
    ),
    AppRecord(
        name="OceanStay",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="68a9d798b0aef1e50b7d4684",
    ),
    AppRecord(
        name="BuildQuest",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="6a21e871212139e49db2d1db",
        notes="Name hints at construction; relationship to NoblePort unverified.",
    ),
    AppRecord(
        name="TaskFlow (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68ab851e6057f714aa9068f2",
        duplicate_of="TaskFlow",
        notes="Only a (Copy) exists; no original 'TaskFlow' in the workspace.",
    ),
    AppRecord(
        name="Echoes of Wisdom (Copy)",
        truth_status=TruthStatus.DUPLICATE,
        platform=Platform.BASE44,
        platform_id="68cdec8d440eb5b957e0874b",
        duplicate_of="Echoes of Wisdom",
        notes="Only a (Copy) exists; no original in the workspace.",
    ),
    AppRecord(
        name="untitled",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="69ed15ff4946a46289900ba0",
        notes="Unnamed scratch build.",
    ),
    AppRecord(
        name="untitled",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="69f24cb921f32c9cfaeb6457",
        notes="Unnamed scratch build.",
    ),
    AppRecord(
        name="untitled",
        truth_status=TruthStatus.EXPERIMENT,
        platform=Platform.BASE44,
        platform_id="68aba5aa37d8f6f619d8c69b",
        notes="Unnamed scratch build.",
    ),
)


# ---------------------------------------------------------------------------
# NoblePort-core products named in NP-OS / strategy. These are NOT Base44 apps.
# Some exist as code in THIS repo (verified); some are concepts not yet found
# anywhere (named-absent). This section is what makes "absence in Base44 does
# not prove absence everywhere" precise and auditable.
# ---------------------------------------------------------------------------

CORE_PRODUCTS: tuple[AppRecord, ...] = (
    AppRecord(
        name="Stephanie.ai",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.REPO,
        platform_id="backend/agents/stephanie.py",
        repository="gcagent/nobleport.etf",
        url="/api/ops-brief",
        purpose="Executive coordination layer (advisory only) in NP-OS.",
        production_evidence="Code present in repo; covered by backend test suite.",
        notes="Present as code here. Absent from the Base44 workspace by design.",
    ),
    AppRecord(
        name="GCagent.ai",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.REPO,
        platform_id="backend/agents/gcagent.py",
        repository="gcagent/nobleport.etf",
        url="/api/jobs",
        purpose="Project Operations layer — construction execution in NP-OS.",
        production_evidence="Code present in repo; covered by backend test suite.",
        notes="Present as code here. Absent from the Base44 workspace by design.",
    ),
    AppRecord(
        name="PermitStream.ai",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.REPO,
        platform_id="backend/agents/permit_stream.py",
        repository="gcagent/nobleport.etf",
        url="/api/projects",
        purpose="Permit layer — permits, inspections, compliance in NP-OS.",
        production_evidence="Code present in repo; covered by backend test suite.",
        notes="Present as code here. Absent from the Base44 workspace by design.",
    ),
    AppRecord(
        name="NoblePort Payment Node",
        truth_status=TruthStatus.VERIFIED_EXISTS,
        platform=Platform.REPO,
        platform_id="backend/api/payments",
        repository="gcagent/nobleport.etf",
        url="/api/payments",
        purpose="Financial layer — only layer permitted to release payments (gated).",
        production_evidence="API surface present in repo; payment release is human-gated.",
        notes="Present as code here. Absent from the Base44 workspace by design.",
    ),
    AppRecord(
        name="Kuzo.io",
        truth_status=TruthStatus.NAMED_ABSENT,
        platform=Platform.UNKNOWN,
        purpose=UNVERIFIED,
        notes=(
            "Named in discussion but NOT found in the Base44 workspace nor in "
            "this repo's code. Concept until a source is cited."
        ),
    ),
    AppRecord(
        name="NobleWatch-pro",
        truth_status=TruthStatus.NAMED_ABSENT,
        platform=Platform.UNKNOWN,
        purpose=UNVERIFIED,
        notes=(
            "Named in discussion but NOT found in the Base44 workspace nor in "
            "this repo's code. Concept until a source is cited."
        ),
    ),
)


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApplicationRegistry:
    """The full, self-validating application inventory."""

    apps: tuple[AppRecord, ...]

    def validate(self) -> None:
        """Fail fast on a malformed registry.

        Invariants:
          * Base44 platform ids are unique (the stable key must not collide).
          * Every DUPLICATE row names a ``duplicate_of`` target.
          * Every NAMED_ABSENT row has no platform id (it is, by definition,
            not located anywhere verified).
        """
        seen_base44: set[str] = set()
        for app in self.apps:
            if app.platform is Platform.BASE44:
                if not app.platform_id:
                    raise ValueError(f"Base44 app {app.name!r} missing platform_id")
                if app.platform_id in seen_base44:
                    raise ValueError(
                        f"Duplicate Base44 platform_id {app.platform_id!r} "
                        f"({app.name!r})"
                    )
                seen_base44.add(app.platform_id)

            if app.truth_status is TruthStatus.DUPLICATE and not app.duplicate_of:
                raise ValueError(f"DUPLICATE {app.name!r} missing duplicate_of")

            if app.truth_status is TruthStatus.NAMED_ABSENT and app.platform_id:
                raise ValueError(
                    f"NAMED_ABSENT {app.name!r} should not have a platform_id"
                )

    def base44_apps(self) -> list[AppRecord]:
        return [a for a in self.apps if a.platform is Platform.BASE44]

    def by_status(self, status: TruthStatus) -> list[AppRecord]:
        return [a for a in self.apps if a.truth_status is status]

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for app in self.apps:
            counts[app.truth_status.value] = counts.get(app.truth_status.value, 0) + 1
        base44 = self.base44_apps()
        distinct_base44 = [
            a for a in base44 if a.truth_status is not TruthStatus.DUPLICATE
        ]
        return {
            "totalRows": len(self.apps),
            "base44Total": len(base44),
            "base44DistinctNonCopy": len(distinct_base44),
            "byTruthStatus": counts,
        }

    def to_dict(self) -> dict:
        return {
            "apps": [a.to_dict() for a in self.apps],
            "summary": self.summary(),
        }


APP_REGISTRY = ApplicationRegistry(apps=BASE44_APPS + CORE_PRODUCTS)

# Self-validate at import — a malformed registry must not load silently.
APP_REGISTRY.validate()
