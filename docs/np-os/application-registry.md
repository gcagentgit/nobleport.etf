# NoblePort Application Registry

> A formal, verified inventory of every application across the NoblePort
> ecosystem — built so that **live systems, concepts, and copies are never
> counted as the same thing.**

This document is the human-readable companion to the **canonical registry**.
The machine-readable source of truth lives in code and the two must stay in
lockstep:

| Surface | Location |
| --- | --- |
| Backend registry (authoritative) | `backend/core/app_registry.py` (`APP_REGISTRY`) |
| CSV export (generated, do not hand-edit) | `docs/np-os/application-registry.csv` |
| Tests | `backend/tests/test_app_registry.py` |

The registry validates itself at import (`APP_REGISTRY.validate()`): Base44 ids
must be unique, every `DUPLICATE` must name the original it copies, and every
`NAMED_ABSENT` concept must carry no location. A malformed definition fails
fast.

---

## Why this exists

A builder workspace count is not an inventory. Base44 reports "21 apps," but
that number folds together a real product, several throwaway experiments, and a
pile of `(Copy)` duplicates. Meanwhile the products that actually run the
business — Stephanie.ai, GCagent, PermitStream, the Payment Node — are not in
Base44 at all; they are code in this repository. Counting all of that as one
list produces a number that is true and useless.

This registry replaces the number with **rows that each carry a truth status**,
so copies, concepts, and live systems can never again be added up together.

---

## Truth status taxonomy

Every row carries exactly one status. They are **not** interchangeable.

| Status | Meaning | Counts as a product? |
| --- | --- | --- |
| `verified_exists` | Existence proven by an authoritative source (Base44 API listing, or code in this repo). Proves existence — **not** deployment or production. | Yes |
| `duplicate` | A name-copy of another registered app (a Base44 `(Copy)`). | No |
| `experiment` | Present in a workspace but judged a template / experiment / unrelated build. | No |
| `named_absent` | Referenced by name in NoblePort docs/strategy but **not found** in any verified source. A concept. | No |
| `unverified` | Existence asserted somewhere but not yet checked. | Pending |

Columns we cannot verify from an authoritative source — URL, environment,
production evidence — are recorded as the literal `UNVERIFIED` sentinel, never
guessed. An honest blank beats a confident wrong cell.

---

## Provenance

The 21 Base44 rows were read directly from the Base44 API (`list_user_apps`) on
**2026-06-26**. Base44 **ids** are the stable keys; names duplicate freely, ids
do not. The Base44 API exposes name and id only — so URL, deployment,
environment, and production evidence for those rows are `UNVERIFIED` pending a
manual check against the builder console / hosting provider.

---

## Base44 workspace — 21 apps (verified)

### NoblePort-core (clearly named) — 1 product + 1 copy

| App | Base44 ID | Status |
| --- | --- | --- |
| Nobleport Nexus | `68ace5b69c57f0a42e92246f` | verified_exists |
| Nobleport Nexus (Copy) | `68bb29aad4e60929fceffad6` | duplicate |

### Plausibly Web3 / AI — 2 originals + 4 copies

| App | Base44 ID | Status |
| --- | --- | --- |
| ENS Identity Lens | `68aa083c32ee5b441e4b0e12` | verified_exists |
| Stellaris Assets | `68aa191b21654352ac53348f` | verified_exists |
| Stellaris Assets (Copy) | `68aa299ffbd2256c2556f9b7` | duplicate |
| Stellaris Assets (Copy) | `68aa2991e01040cd71a387aa` | duplicate |
| CryptoPulse AI (Copy) | `68ab857a69e17e178f1971b0` | duplicate¹ |
| CryptoChart AI (Copy) | `68ab85dd565d5e8cc50800f1` | duplicate¹ |

¹ Only a `(Copy)` exists in the workspace — there is **no original** named
"CryptoPulse AI" or "CryptoChart AI" present.

### Likely experiments / templates / unrelated — 13

| App | Base44 ID | Status |
| --- | --- | --- |
| AquaHut | `68a9fd15179e8fd07373ef5b` | experiment (3 copies) |
| AquaHut (Copy) | `68d67e7711c551c2152abd14` | duplicate |
| AquaHut (Copy) | `68aa045bc9793caf6c241f5f` | duplicate |
| AquaHut (Copy) | `68aa08abbf77d9233404f89a` | duplicate |
| HydroTracker | `68a9d7142597cfe16d0d45f8` | experiment |
| HydroTracker (Copy) | `68e1b97a4a98c2175cae7130` | duplicate |
| OceanStay | `68a9d798b0aef1e50b7d4684` | experiment |
| BuildQuest | `6a21e871212139e49db2d1db` | experiment |
| TaskFlow (Copy) | `68ab851e6057f714aa9068f2` | duplicate |
| Echoes of Wisdom (Copy) | `68cdec8d440eb5b957e0874b` | duplicate |
| untitled | `69ed15ff4946a46289900ba0` | experiment |
| untitled | `69f24cb921f32c9cfaeb6457` | experiment |
| untitled | `68aba5aa37d8f6f619d8c69b` | experiment |

**Base44 honest count:** 21 total · 1 clearly-named NoblePort-core product
(Nobleport Nexus) · the rest are Web3/AI experiments, generic experiments, and
12 duplicates.

---

## NoblePort-core products (NOT Base44 apps)

These are named in NP-OS / strategy. **Absence from Base44 is not absence
everywhere** — most exist as code in *this* repository.

| Product | Status | Location | Note |
| --- | --- | --- | --- |
| Stephanie.ai | verified_exists | `backend/agents/stephanie.py` (`/api/ops-brief`) | Code here; absent from Base44 by design |
| GCagent.ai | verified_exists | `backend/agents/gcagent.py` (`/api/jobs`) | Code here; absent from Base44 by design |
| PermitStream.ai | verified_exists | `backend/agents/permit_stream.py` (`/api/projects`) | Code here; absent from Base44 by design |
| NoblePort Payment Node | verified_exists | `backend/api/payments` (`/api/payments`) | Code here; payment release is human-gated |
| Kuzo.io | **named_absent** | — | Not in Base44, not in this repo. Concept until a source is cited. |
| NobleWatch-pro | **named_absent** | — | Not in Base44, not in this repo. Concept until a source is cited. |

---

## What is still `UNVERIFIED` (the real backlog)

The registry deliberately does **not** invent these. To raise a Base44 row from
`verified_exists` to verified-in-production, collect and record:

1. **URL** — the live preview / custom domain, per app.
2. **Replit / Manus locations** — any builds living outside Base44 and this repo.
3. **Production evidence** — deployment status, traffic, or a working endpoint.
4. **Environment** — dev / staging / production, per app.
5. **Owner & integration dependencies** — who maintains it and what it calls.
6. **Kuzo.io / NobleWatch-pro** — cite a source or keep them `named_absent`.

---

## Keeping the mirrors in sync

`backend/core/app_registry.py` is authoritative and self-validating — edit it
first. Then regenerate the CSV from the registry (never hand-edit the CSV) and
update the counts in this doc and in `backend/tests/test_app_registry.py` if a
verified re-read of a workspace genuinely moves them. The Base44 count of 21 is
pinned in the tests on purpose: if it changes, the workspace changed, and the
registry must be **re-read from the API**, not nudged to match.
