# NoblePort Web3 Workspace

This folder holds everything web3-adjacent: smart contracts, ENS/DID
resolvers, SSI architecture, the NoblePort ETF bridge, and the NemoClaw
governance/signing components.

It is **deliberately separated** from the real-world construction
operating system that lives in `backend/` and `src/` at the repo root.

## What's in here

```
web3/
├── contracts/                 — Solidity smart contracts
│   ├── HumanApprovalGateway.sol
│   └── MassachusettsBuildingPermits.sol
│
├── backend/                   — Python web3 modules
│   ├── api/bridge.py          — FastAPI routes for the ETF bridge
│   └── services/nobleport_bridge.py
│
└── frontend/                  — TypeScript / React web3 modules
    ├── lib/
    │   ├── ensDidResolver.ts
    │   ├── stephanieAI.ts     — TS Stephanie that fronts MCP + ENS/DID
    │   └── nemoclaw/          — governance, signer gateway, audit policy
    └── components/
        ├── NoblePortSSIArchitecture.tsx
        └── StephanieAINetworkHub.tsx
```

## The Boundary

The construction OS (in `backend/` and `src/`) does **not** import from
`web3/`. The build excludes this folder (`.vercelignore`, no Python
imports). Removing this folder entirely would not break the
construction OS.

The web3 workspace **may** depend on construction OS data (e.g. for
permit tokenization, for anchoring trust records on-chain), but those
dependencies flow one direction: web3 → construction, never construction
→ web3.

A few construction models retain *optional* fields that web3 can use as
anchor points:

- `backend/models/project.py` — `permit_token_id`, `permit_tx_hash`
- `backend/models/trust_record.py` — `chain_anchor`

These are nullable. The construction OS does not require them.

## Why separate?

The real revenue product is construction operations: leads → estimates
→ deposits → permits → builds → invoices → maintenance. That product
works on its own.

Web3 (ETF tokenization, SSI, on-chain audit anchoring) is a separate
layer that can sit beside it for investors and governance, without
contaminating the operational core.

## Re-activating web3

To bring web3 components back into the main application:

1. Move desired backend modules from `web3/backend/` back into
   `backend/api/` / `backend/services/`.
2. Move desired frontend modules from `web3/frontend/lib/` back into
   `src/lib/`.
3. Re-register routers in `backend/main.py`.
4. Remove `web3/` from `.vercelignore` and `vercel.json` ignore list.

Until then, this workspace is dormant.
