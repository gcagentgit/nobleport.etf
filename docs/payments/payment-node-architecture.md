# NoblePort Payment Node Architecture

Stripe Connect and PayPal are **separate payment processors**. They do not
connect to each other, and NoblePort never routes money from one into the
other — doing so would stack fees, add reconciliation surface, and break the
audit trail for deposits and progress payments.

Instead, both processors settle into a single **NoblePort Payment Node**, which
is the one source of truth for the construction ledger.

```
Customer
   │
   ├── Stripe Checkout ──► Stripe (Connect)  ─┐
   │                                          │
   └── PayPal Checkout ──► PayPal Business ───┤
          (PayPal / Venmo / card)            │
                                             ▼
                                  NoblePort Payment Node
                                  (single source of truth)
                                             │
              ┌──────────────┬───────────────┼───────────────┐
              ▼              ▼               ▼               ▼
        Project Ledger   Job Costing   Cash Position    CFO Console
```

## Why two independent processors

| Processor | Role | Best for |
|-----------|------|----------|
| **Stripe** | Primary construction processor | Deposits, progress billing, change orders, ACH, escrow-style controls |
| **PayPal / Venmo** | Secondary consumer processor | Consumer convenience, Venmo users, quick invoices, one-time purchases |

Keeping them parallel means each customer can pay the way they prefer, while the
business keeps clean, processor-segmented books.

## The node is the single source of truth

Every settled payment — regardless of processor — is applied to the underlying
Job (and Change Order) by one shared routine,
`PaymentNode.apply_settlement()` in
[`backend/services/payment_node.py`](../../backend/services/payment_node.py).

That routine owns the **deposit-before-start gate**: a job stays in
`PENDING_DEPOSIT` until cleared deposits meet or exceed the required amount, at
which point it flips to `SCHEDULED`. Because both the Stripe webhook handler and
the PayPal webhook handler call the same routine, the gate behaves identically
no matter how the customer paid. Totals, margin, and change-order balances are
recalculated in that same place.

## Components

| Layer | File | Responsibility |
|-------|------|----------------|
| Model | `backend/models/payment.py` | `PaymentProcessor` enum (now includes `paypal`, `venmo`), plus `paypal_order_id` / `paypal_capture_id` / `payment_method` columns |
| Stripe | `backend/services/stripe_service.py` | Stripe Checkout sessions + webhooks; delegates settlement to the node |
| PayPal | `backend/services/paypal_service.py` | PayPal Orders v2 + webhooks; delegates settlement to the node |
| Node | `backend/services/payment_node.py` | Shared settlement logic + unified ledger / cash-position reporting |
| API | `backend/api/payments.py` | Stripe + PayPal checkout and webhook endpoints |
| API | `backend/api/payment_node.py` | Unified ledger + cash-position endpoints |

## Endpoints

**Checkout (Stripe)**
- `POST /api/payments/checkout/deposit`
- `POST /api/payments/checkout/progress`
- `POST /api/payments/checkout/change-order`

**Checkout (PayPal / Venmo)**
- `POST /api/payments/paypal/order/deposit`
- `POST /api/payments/paypal/order/progress`
- `POST /api/payments/paypal/order/change-order`

**Webhooks**
- `POST /api/payments/webhook/stripe`
- `POST /api/payments/webhook/paypal`

**Unified node (single pane of glass)**
- `GET /api/payment-node/summary` — cross-processor cash position + per-processor breakdown
- `GET /api/payment-node/ledger` — unified, chronological ledger (filter by `processor` / `status`)

## Venmo

Venmo settles through PayPal Checkout as a funding source. When a capture
reports a Venmo funding source, the payment's `processor` is recorded as
`venmo` (and `payment_method` as `venmo`) so it can be reconciled separately,
while still flowing through the single PayPal integration.

## Configuration

Backend settings (env prefix `NOBLEPORT_`):

```
# Stripe
NOBLEPORT_STRIPE_SECRET_KEY=
NOBLEPORT_STRIPE_WEBHOOK_SECRET=

# PayPal / Venmo
NOBLEPORT_PAYPAL_CLIENT_ID=
NOBLEPORT_PAYPAL_CLIENT_SECRET=
NOBLEPORT_PAYPAL_WEBHOOK_ID=
NOBLEPORT_PAYPAL_ENVIRONMENT=sandbox   # or "live"
```

## What we deliberately did NOT build

- **No Stripe→PayPal or PayPal→Stripe money movement.** They remain separate
  rails. The only thing they share is the node they report into.
- **No co-mingled balances.** The node keeps a per-processor breakdown so books
  stay processor-segmented and audit-friendly.
