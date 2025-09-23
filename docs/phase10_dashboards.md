# Phase 10 — Dashboard API & KPI Views

This document describes the new dashboard endpoints under `/dash`, security scoping, database views, and Makefile helpers introduced in Phase 10.

## Overview

- Endpoints live under `apps/hive_api/routers/dash.py`.
- Secured via `apps/hive_api/security.py` with org/brain scoping.
- Queries prefer Postgres SQL view `v_dash_sales_kpis` with graceful fallback to inline SQL on other dialects (e.g., SQLite).
- Router is wired in `apps/hive_api/main.py`.

## Endpoints

- `/dash/kpis`
  - Returns: orders, net revenue, average order value (AOV)
  - Params (optional): `org_id`, `brain_id`
  - Source: Postgres view `v_dash_sales_kpis` if available; otherwise inline aggregation from `order` table.

- `/dash/orders/summary`
  - Returns: counts of orders by status
  - Params (optional): `org_id`, `brain_id`

Both endpoints enforce scoping via `SubjectScope.ensure_scope()` using `org_id` and `brain_id`.

## Security & Scoping

Defined in `apps/hive_api/security.py`:

- `SubjectScope(sub, role, org_id, brain_ids)`
  - `ensure_scope(req_org_id, req_brain_ids)` ensures the caller is permitted to access requested org/brain scopes.
  - `require_role(min_role)` helper for role checks (currently not required by Phase 10 endpoints).
- Dependencies:
  - `get_subject_scope()` — strict JWT validation (Bearer token required)
  - `get_subject_scope_optional()` — dev-friendly: if a Bearer token is present it is validated; if not, a permissive readonly scope is provided in dev/debug.

## Database Migration

Alembic revision: `alembic/versions/abcdef123456_phase10_dash_views.py`

- Creates Postgres SQL view `v_dash_sales_kpis` for fast KPI queries.
- No-op on SQLite to keep local/dev friction low.
- Downgrade drops the view when using Postgres.

View schema (conceptual):

- Columns: `org_id`, `brain_id`, `orders`, `net_revenue_cents`, `aov_cents`

## Running Locally

1. Apply latest migrations:
   ```bash
   make migrate-up
   ```
2. Start the API locally (dev):
   ```bash
   make api-local
   # API default: http://127.0.0.1:8001
   ```
3. Hit endpoints (org/brain are optional):
   ```bash
   make dash-kpis ORG=<org_uuid> BRAIN=<brain_uuid>
   make dash-orders ORG=<org_uuid> BRAIN=<brain_uuid>
   ```

End-to-end backtest for Phase 10:
```bash
make phase10-backtest
```

## Auth Notes

- Dev mode: Endpoints work without a Bearer token via `get_subject_scope_optional()`.
- Non-dev/staging/prod: Provide a JWT with `sub`, `role`, `org_id`, and optional `brain_ids` claims.

Example header:
```http
Authorization: Bearer <jwt>
```

## Extensibility

- Consider materialized views and indexes for high-traffic Postgres deployments.
- Add tests covering:
  - view-backed path vs. fallback path
  - scoping rules (org-only, brain-only, both)
  - auth required vs. optional modes

## Files Touched

- `apps/hive_api/routers/dash.py` — new router and endpoints
- `apps/hive_api/security.py` — scoping/authorization helpers
- `apps/hive_api/main.py` — router inclusion
- `alembic/versions/abcdef123456_phase10_dash_views.py` — KPI view
- `Makefile` — helper targets: `dash-kpis`, `dash-orders`, `phase10-backtest`
