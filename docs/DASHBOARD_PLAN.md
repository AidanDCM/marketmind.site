# Dashboard Expansion Plan (Profit + Incidents)

Last updated: 2025-09-07T12:33:56-04:00

## Goals
- Expose safety KPIs and profit levers in a single operator console.
- Provide one-click operational playbooks (freeze/unfreeze, promote winner, rollback, submit appeal).
- Maintain strict RBAC scope and audit trails for all actions.

## Pages

1) Overview (`apps/console/app/pages/overview.tsx`)
- Tiles:
  - Publish Success %
  - Valid Tracking Rate (VTR) % / Order Defect Rate (ODR) %
  - Reconciliation % and Cash Runway (days)
  - Profit Uplift (by module)
  - Queue depth and error rate
- Data sources:
  - `GET /dash/kpis`
  - `GET /health/summary`
  - Sheets echoes for profit modules (optional)

2) Profit (`apps/console/app/pages/profit.tsx`)
- Tiles:
  - Profit Uplift by module (bundles, coupons, variation, fees, pruning)
  - Active experiments and rollouts (pricing, content)
  - Growth Governor gates (green/red)
- Tables:
  - `profit_modules_log` view (timestamp, module, action, guardrail checks, outcome)
- Actions (buttons with RBAC admin/editor):
  - Run bundle builder (SIM/canary)
  - Toggle coupons (org/brain scoped)
  - Trigger variation consolidation analysis
- Endpoints to read:
  - `GET /marketing/experiments` (active)
  - `GET /learning/rollouts`
  - `GET /learning/metrics`, `GET /learning/benchmarks`
  - `GET /finance/forecast`

3) Incidents (`apps/console/app/pages/incidents.tsx`)
- Grid:
  - Open incidents with severity, Suggested Fix, one-click action link
- Playbooks mapped to incidents:
  - API 429/5xx: backoff/shrink/open circuit → resume conservative
  - Schema drift: shadow adapter → promote fix/rollback
  - Supplier OOS/late: failover/pause → approve alternate
  - Carrier reject: update carrier map + re-post
  - MAP/parity red: block publish + compliant price
  - Suppression: auto-pause + appeal pack → submit
  - Margin erosion: tighten undercut; lock floor 7d
  - Cash squeeze: freeze expansion; prune non-core SKUs
- Endpoints:
  - Governance: `GET /orchestrator/health` (freeze states), `GET /health/summary`
  - Compliance: `POST /compliance/lint/prepublish`, `POST /compliance/scan/postpublish`
  - Operator actions (protected): `POST /orchestrator/freeze/{brain}`, `POST /learning/rollouts/promote`

4) Pricing (`apps/console/app/pages/pricing.tsx`)
- Tiles: Floor vs. live vs. proposed, MAP/parity compliance, publish success
- Tables: Pending approvals, recent changes
- Endpoints: `GET /pricing/pending`, `GET /pricing/approved`, `GET /pricing/history`

5) Learning (`apps/console/app/pages/learning.tsx`)
- Tiles: Drift alerts, benchmark scores, rollout phases
- Tables: Model versions, metrics
- Actions: Retrain, Promote (RBAC admin/editor)
- Endpoints: `/learning/*`

6) Marketing (`apps/console/app/pages/marketing.tsx`)
- Tiles: TACoS / ROAS, budget usage, stop-loss triggers
- Tables: Campaigns, assets, experiments, variants, bundles
- Endpoints: `/marketing/*`

7) Finance (`apps/console/app/pages/finance.tsx`)
- Tiles: Recon %, cash buffer (days), sweep readiness
- Tables: Ledger entries/batches, invoices, recon tasks
- Endpoints: `/finance/*`

## UX Standards
- RBAC scope from JWT → `org_id`, `brain_id` applied to all queries.
- Idempotent POSTs; show explainability/logs on write.
- Error banners for any gate breached; freeze actions surfaced prominently.

## API Contracts (selected)
- Dashboard KPIs: `GET /dash/kpis`, `GET /dash/orders/summary`
- Profit log (to add): expose `profit_modules_log` via read-only endpoint (future)
- One-click actions:
  - `POST /orchestrator/freeze/{brain}` body: `{ "freeze": true | false }`
  - `POST /learning/rollouts/promote` body: `{ "rollout_id": n, "phase": "canary|prod" }`

## Implementation Plan
- Step 1: Wire overview/profit/incidents pages with read-only KPIs (server-side fetch, SWR for refresh)
- Step 2: Add RBAC-guarded action buttons (freeze, promote) with success toasts and audit log display
- Step 3: Add profit_modules_log exposure endpoint and tile
- Step 4: Add Sheets echo status badges for governance/compliance artifacts

## Acceptance
- Page renders without errors under dev auth
- RBAC enforced; actions require admin/editor
- SLO tiles visible: Publish≥99.5%, VTR≥98%, Recon≥99%, ODR<0.6%
- One-click actions write audit entries and surface explainability strings
