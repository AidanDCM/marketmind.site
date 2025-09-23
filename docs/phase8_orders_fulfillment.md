# Phase 8 — Orders Intake, Tax & Fulfillment Routing

Status: intake aligned + idempotency added + optimistic concurrency guards; tax model seam wired; routing guardrails + address validation added; CJ PO idempotency implemented (simulated); fulfillment label seam + publish stub implemented; endpoints wired; KPIs DB-backed.

## Scope
- Channel-agnostic Order State Machine (OSM)
- Tax engine: marketplace vs seller-collected, jurisdiction tables (seam)
- Routing engine: supplier selection + rate-shop seam + guardrails
- PO creation: CJ (seam and idempotency) + AutoDS (optional seam)
- Fulfillment: label purchase seam; publish tracking to channels
- Exceptions: OOS, ADDRESS_FAIL, PARTIAL, DELAY, CANCEL/REFUND, RETURN (playbooks)
- KPIs/alerts: LSR, VTR, ODR
- API endpoints for CS/ops
- Tests + verify scripts + backtests

## Endpoints (current)
- `GET /orders/{id}` — order detail stub (DB alignment next)
- `POST /orders/{id}/reprocess` — queues reprocess (stub)
- `POST /orders/{id}/route` — uses `RoutingEngine` guardrails + address validation; returns carrier/service and supplier id
- `POST /orders/{id}/po` — uses `CJPOClient` with idempotency key; returns `supplier_po_ref` and `idempotency_key`
- `POST /orders/{id}/fulfill` — uses `FulfillmentService` to buy label (simulated) and publish tracking (stub)
- `POST /orders/{id}/cancel` — cancel stub
- `POST /orders/{id}/refund` — refund stub
- `POST /orders/{id}/exception` — opens exception via `ExceptionsService`
- `GET /orders/kpis` — returns DB-backed KPIs via `KPIService.compute(db)`

Wire-in: `apps/hive_api/main.py` includes `apps.hive_api.routers.orders.router`.

## Modules
- `packages/orders/intake.py` — aligned with `packages/database/models/order.py` fields/enums; uses `calculate_with_model()` for Phase 8 tax model; idempotency key computed and stored to prevent duplicate creates; optimistic concurrency (CAS) guard via `expected_updated_at`; appends lightweight audit trail to `Order.meta` for transitions.
- `packages/orders/tax.py` — `calculate_with_model(tax_model, provider)` with provider seam; rules-based fallback.
- `packages/orders/routing.py` — routing engine with stricter address validation, guardrails (`max_cost_cents`) and simple rate-shopping.
- `packages/orders/po_cj.py` — CJ PO client with idempotent `create_po()` and tracking polling stub.
- `packages/orders/fulfillment.py` — label purchase seam (simulated) + tracking publish stub.
- `packages/orders/kpis.py` — DB-backed KPI computation (LSR, VTR, ODR) over a rolling window (defaults: SLA=2 days, window=60 days).

## Testing & Backtesting
- Makefile targets:
  - `phase8-tests-nocov` — runs Phase 8 tests without coverage gating
  - `verify-phase8` — runs `scripts/verify_integrations.sh` (expects API running on :8001)
  - `backtest-phase8` — migrate + verify + short load test
- Unit tests added:
  - `tests/orders/test_tax.py` — marketplace vs seller collected
  - `tests/api/test_orders_endpoints.py` — endpoint presence and basic responses
  - `tests/orders/test_routing.py` — address validation and guardrails
  - `tests/orders/test_po_cj.py` — idempotent PO creation and tracking shape
- E2E lifecycle tests recommended: idempotency on intake and replays, exception flows (OOS, ADDRESS_FAIL), PO idempotency, fulfillment/tracking publish, KPI correctness.

### Quickstart
1. Start API: `make api-local`
2. In another terminal, run tests: `make phase8-tests-nocov`
3. Verify integrations (API must be running): `make verify-phase8`
4. Optional backtest: `make backtest-phase8`

## Runbook (initial)
- Stuck orders: reprocess via `POST /orders/{id}/reprocess`.
- Open exception: `POST /orders/{id}/exception` with `{ "kind": "OOS", "note": "..." }`.
- KPIs: `GET /orders/kpis` now DB-backed; if empty datasets, defaults avoid division by zero.
- Auth: Orders endpoints support optional auth in development. Set `ORDERS_REQUIRE_AUTH=true` to enforce bearer authentication in production. Audit logs include who/what metadata.

## Configuration
- `TAX_PROVIDER`: `none|taxjar|avalara` (default `none`) — provider seam active; rules fallback when external providers not configured.
- CJ: `CJ_API_KEY` (optional; when absent simulation is used).
- Shipping: `EASYPOST_API_KEY` or `SHIPPO_API_KEY` (optional; when absent simulation is used).
- `tax_model` per order payload or inferred by channel (`marketplace_collected` vs `seller_collected`).
- Orders API auth: `ORDERS_REQUIRE_AUTH` (default `false`). When `true`, endpoints require valid bearer tokens; when `false`, anonymous access is allowed for local dev and verification.

## Next
- Complete OSM alignment across DB enums and intake (CAS guards done; expand transitions as needed for channels).
- Integrate CJ API and shipping label providers (feature-flagged) with retries/backoff and idempotency keys.
- Implement channel-specific tracking publish adapters.
- Dashboards using DB-backed KPI snapshots.
- Expand unit/contract/integration tests with failure injection and performance runs.
