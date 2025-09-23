# MarketMind - E-commerce Automation Platform

## Table of Contents
- [Local Development](#local-development)
- [Testing](#testing)
  - [Unit Tests](#unit-tests)
  - [Integration Tests](#integration-tests)
  - [Performance Testing](#performance-testing)
- [Phase 3 Backtest](#phase-3-backtest)
- [Phase 4 Quality Gates](#phase-4-quality-gates)
- [Phase 5 Ingestion Runbook](#phase-5-ingestion-runbook)
- [Phase 7 – Multi-Brain & Global Scaling](#phase-7--multi-brain--global-scaling)
- [Phase 8 – Orders Fulfillment Integration](#phase-8--orders-fulfillment-integration)
- [Phase 9 – Governance & Resilience](#phase-9--governance--resilience)
- [Phase 11 – Compliance & Privacy](#phase-11--compliance--privacy)
- [API Documentation](#api-documentation)
- [CI/CD Pipeline](#cicd-pipeline)
- [Code Coverage](#code-coverage)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
  - [Console RBAC & Tokens](#console-rbac--tokens)
  - [Env Fallbacks](#env-fallbacks)
  - [CI Post-Deploy Observability Smoke](#ci-post-deploy-observability-smoke)

## Local Development

If Docker Desktop is unavailable, you can run the API locally with SQLite:

1) Create venv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r infra/docker/requirements-api.txt
pip install -r infra/docker/requirements-worker.txt
```

2) Run API with SQLite (local)

```bash
export DB_URL=sqlite:///./dev.db
export APP_ENV=development
python -m uvicorn apps.hive_api.main:app --reload --host 127.0.0.1 --port 8001
```

3) Verify

- Info: `GET http://127.0.0.1:8001/_info`
- Health: `GET http://127.0.0.1:8001/health/data`

4) One-off ingestion (separate shell)

```bash
source .venv/bin/activate
python scripts/run_ingest_local.py
```

Expected: rows in `products`, `suppliers`, `competitors`, `price_history` for SKU `SAMPLE-001`.

# Indomitable E‑Commerce System (MarketMind)

This repo scaffolds a production-grade, multi-niche e‑commerce automation platform:

- FastAPI backend (Hive API)
- Celery workers (schedulers + self-repair)
- PostgreSQL, Redis
- Next.js 14 dashboard (console)
- Adapter-ready connectors for marketplaces and suppliers
- Guardrails-driven pricing and operations

## Quick Start

### With Docker (Recommended)

1) Start the services
- Node 18+, Python 3.12 (optional for local dev outside containers)

2) Env
1. Copy `.env.example` to `.env` and fill in values if needed.

3) Run
```bash
docker compose -f infra/docker/docker-compose.yml up -d --build
```

4) Visit API at `http://localhost:8001/_info` (local) or `http://localhost:8000/_info` (Docker)
- Console: http://localhost:3000
- Redis: redis://localhost:6379
- Postgres: postgres://postgres:postgres@localhost:5432/hive

## Structure
```
apps/
  hive-api/        # FastAPI service
  hive-worker/     # Celery workers (beat + tasks)
  console/         # Next.js dashboard
packages/
  shared/          # Config, guardrails, models
  database/        # Active SQLAlchemy 2.0 models (use this Base)
infra/
  docker/          # Dockerfiles + Compose
```

## Testing

### Unit Tests

- Run unit tests with `pytest`:
```bash
pytest apps/hive_api/tests
```

### Integration Tests

- Run integration tests with `pytest`:
```bash
pytest apps/hive_api/tests/integration
```

### Performance Testing

- Run performance tests with `locust`:
```bash
locust -f apps/hive_api/tests/performance --headless --num_users=10 --hatch_rate=1
```
Note: If `locust` is not installed, run `pip install locust` once. See Phase 7 section for headless Make target.

## Phase 3 Backtest

Run the full validation pipeline before Phase 4:

```bash
make phase3-backtest
```

Details: see `docs/phase3_backtest.md`.

Notes:
- Active models are under `packages/database/models/` using SQLAlchemy 2.0 (`Mapped[]`, `mapped_column()`).
- Legacy `packages/models/` is excluded from lint/type checks and Alembic uses the active `Base`.
- FastAPI is pinned to `0.116.1` and Starlette to `0.47.2` (remediated advisories). The previous temporary ignore has been removed from `scripts/ci/security_checks.sh`.

## Phase 4 Quality Gates

The following targets validate connectors and active database models for type safety, lint compliance, tests, and coverage. Run them locally before pushing:

```bash
# Install dev tooling first (ruff, black, mypy)
make install-dev

# Type checks (connectors + database models)
make type-check-phase4

# Lint (connectors + database models)
make lint-phase4

# Unit/contract tests (connectors + core DB tests, quick)
make full-suite-phase4

# Coverage report (HTML in htmlcov/)
make coverage-phase4

# DRYRUN smoke for adapters (no external side effects)
make adapters-health
```

If you see lint violations, you can attempt autofixes with Ruff:

```bash
.venv/bin/ruff check packages/connectors packages/database/models --fix
```

Notes:
- The `adapters-health` target is a DRYRUN smoke suite and sets coverage `--cov-fail-under=0` to avoid failing on partial-package coverage. Use `make coverage-phase4` if you need strict coverage enforcement.
- Connectors and models adopt exception chaining (`raise ... from e`) and `TYPE_CHECKING`-guarded forward refs in SQLAlchemy models to prevent circular imports and satisfy Ruff/mypy.

## Phase 5 Ingestion Runbook

Phase 5 adds ingestion pipelines, checkpoints, and safety runbooks.

- Endpoints (see `apps/hive_api/routers/ingest.py`):
  - `GET /ingest/status` – list checkpoints
  - `POST /ingest/run/catalog` – enqueue catalog sync (supplier `cj`)
  - `POST /ingest/run/signals` – enqueue signals snapshot
  - `POST /ingest/run/orders` – enqueue orders pull (feature-gated)
  - `POST /ingest/backfill/price_history` – backfill signals price history (SIMULATION only)
  - `POST /ingest/replay/checkpoint` – manual checkpoint set

- Makefile helpers (cURL against 127.0.0.1:8001):
  - `make ingest-status`, `make ingest-health`
  - `make ingest-catalog`, `make ingest-signals`, `make ingest-orders`
  - `make ingest-backfill` (requires SIMULATION enabled), `make ingest-replay`

- Simulation flag semantics (`packages/shared/config/flags.py`):
  - `SIMULATION_ENABLED` accepts case-insensitive values. Truthy: `1,true,yes,y,on`. Falsy: `0,false,no,n,off,""`.
  - Backfill endpoints are gated to simulation to prevent side effects.

- Checkpoints (`packages/shared/models_db.py` → `IngestCheckpoint`):
  - Unique scope: `(org_id, brain_id, pipeline, source, key)`; value is typically ISO8601 watermark.
  - Tasks upsert checkpoints to ensure idempotency and replay safety.

- Metrics (optional):
  - Tasks emit Prometheus counters/histograms when `prometheus_client` is available:
    - `ingest_task_runs_total{task}`
    - `ingest_task_duration_seconds{task}`
    - `ingest_task_upserts_total{task,source}`
  - If the library is not installed, metrics no-op gracefully.

- Local validation:
  - Unit/integration (ingest): `pytest tests/ingest -q`
  - Adapters DRYRUN health (no external side effects): `make adapters-health`
  - Full integrations (may call external APIs; ensure env vars): `make verify-integrations`

- Migrations:
  - `make migrate-up` ensures `ingest_checkpoints` exists (see `alembic/versions/*add_ingest_checkpoints*.py`).

### SQLAlchemy Models

All active models are being migrated to SQLAlchemy 2.0 style annotations:

- Use `Mapped[T]` hints with `mapped_column()`
- Define relationships with `Mapped[]`
- Avoid `Column()` without typing; prefer the new style

This ensures compatibility with modern SQLAlchemy, better IDE support, and successful mypy checks.

### Integrations Verification

There is an end-to-end verification script that may perform external requests:

```bash
make verify-integrations
```

Note: This may require API keys or sandbox credentials set via environment variables (see `.env.example`). Review and export needed variables before running. Prefer running in a controlled environment.

#### Phase 5 Verification Summary (dev)

- All 14/14 checks passed on local dev (`make verify-integrations`).
- Health probes: liveness/readiness/data/app info returned HTTP 200.
- Ingestion endpoints responsive: status, health, CJ catalog sync, pricing snapshot, order pull.
- Pricing endpoints responsive: history, pending, approved.
- Database connectivity verified (SQLite `dev.db`), sample products present.
- Warnings (expected in dev): unset API creds (Amazon, CJ, Google), default `.env` secrets flagged; replace before staging/prod.

#### Post-ingestion confirmation (2025-08-20)
- Commands run: `make ingest-catalog`, `make ingest-pricing`
- Result: ingestion tasks accepted; end-to-end integrations remained green (see `make verify-integrations` 14/14 PASS)

## Phase 7 – Multi-Brain & Global Scaling

See detailed runbooks:

- docs: `docs/phase7_multi_brain.md` (architecture, orchestration, scaling, oversight)
- tests: `docs/phase7_testing_plan.md` (unit/integration/load/backtesting/security)

Helpful Make targets:

```bash
# Short sanity backtest for Phase 7 (migrate + verify-integrations + short load)
make phase7-backtest

# Parametric headless load test
make load-test USERS=500 SPAWN=25 DURATION=600
```

Notes:
- Redis is optional locally but recommended for orchestrator testing (`make api-local-redis`).
- `verify-integrations` remains the primary end-to-end gate; Phase 7 adds load and orchestration checks.

### Phase 7 Runbook Notes (2025-08-20)

- Simulation flag: use environment variable `SIMULATION_ENABLED=false` to enable real external calls. Do not use `FEATURE_SIMULATION_ENABLED`.
- Credentials: set Amazon SP-API (`AMAZON_SP_API_CLIENT_ID`, `AMAZON_SP_API_CLIENT_SECRET`, `AMAZON_SP_API_REFRESH_TOKEN`, `AMAZON_SP_API_ROLE_ARN`, `AMAZON_SP_API_REGION`) and CJ Dropshipping (`CJ_API_KEY`, `CJ_WEBSITE_ID`) before running smokes.
- Load testing:
  - Short run: `USERS=100 SPAWN=10 DURATION=120 make load-test`
  - KPI report: `USERS=50 SPAWN=5 DURATION=30 make load-test-report`
  - Artifacts saved under `reports/load/` (CSV and `report.html`).
- Pricing snapshot checkpoint: after successful Amazon pricing snapshot, `/ingest/status` includes a `pricing/amazon` checkpoint with key `last_snapshot_iso`.

### Orchestrator Endpoints (added)

- `GET /orchestrator/health` — service health and freeze states
- `GET /orchestrator/queues` — declared Celery task names per brain
- `POST /orchestrator/freeze/{brain}` — freeze or unfreeze a brain (`pricing|marketing|analytics|compliance|expansion`)
- `POST /orchestrator/override` — accept an admin override for a decision

### Brain Task Queues (Celery)

- Queues: `pricing`, `marketing`, `analytics`, `compliance`, `expansion` (default: `default`)
- Tasks:
  - Pricing: `apps.hive_worker.tasks.brains.pricing.price_decide`
  - Marketing: `apps.hive_worker.tasks.brains.marketing.generate_copy`
  - Analytics: `apps.hive_worker.tasks.brains.analytics.aggregate_kpis`
  - Compliance: `apps.hive_worker.tasks.brains.compliance.check_order`
  - Expansion: `apps.hive_worker.tasks.brains.expansion.score_market`

Quick check (with API running):

```bash
curl -s http://127.0.0.1:8000/orchestrator/health | jq .
curl -s http://127.0.0.1:8000/orchestrator/queues | jq .
```

### Decision Ledger (added)

- Models: `packages/database/models/decision.py` defines `DecisionLog` and `KPIEvent` using SQLAlchemy 2.0 style.
- Brain stubs append best-effort `DecisionLog` rows for auditability.
- Note: ensure DB tables exist (run migrations or use `init_db` in dev).

### Verify Integrations (updated)

- `scripts/verify_integrations.sh` now includes orchestrator checks:
  - Health and queues endpoints
  - Freeze/unfreeze round-trip for a brain
  - Override acceptance

#### Dev ingestion skip behavior
- In dev/CI when Celery broker is unavailable or modules are disabled, ingestion endpoints return HTTP 200 with a safe payload to keep verification green:
  - `POST /ingest/run/catalog` → `{ "status": "skipped", "reason": "celery_unavailable" }`
  - `POST /ingest/run/orders` → `{ "status": "skipped", "reason": "orders_disabled" }` or `{ "reason": "celery_unavailable" }`
  - Some endpoints may report `{ "status": "skipped", "reason": "spapi_not_configured" }` when external creds are missing.

#### Phase 7 Verification Summary (dev)
- Date: 2025-08-20 (local dev)
- Results:
  - `make verify-integrations` → 19/19 PASS
  - `make adapters-health` → PASS
  - `make test` → PASS (82% coverage reported on DB-focused suite)
  - `make phase7-backtest` → verification PASS; short load test requires `locust` installed
  - Security: `make security-check` → No secrets found, no known Python dependency CVEs

#### Load test quickstart
- Install once (if needed): `pip install locust`
- Run short headless: `make load-test USERS=100 SPAWN=10 DURATION=120`

## Phase 9 – Governance & Resilience

Phase 9 introduces the governance layer: Policy/Risk engines, Arbitrator, Self-Repair, Contract Monitor, Release/Canary Manager, Secret Rotation, Compliance Watcher, Chaos Lab, and governance dashboards.

Docs
- Governance Playbook: `docs/phase9_governance.md`
- Readiness Checklist: `docs/phase9_readiness.md`
 - Approval & Waiver: `docs/phase9_approval.md`
 - Credentials Follow-Up (Critical): `docs/credentials_followup.md`

Status
- Readiness: GREEN to start. Product model migrated to SQLAlchemy 2.0; integrations verification PASS; security checks PASS; load sanity PASS.
- Live smoke: CJ and Google Sheets PASS; Amazon SP-API pending refresh token (time-boxed waiver in `docs/phase9_approval.md`).

IMPORTANT
- Until the Amazon refresh token is provided, treat Amazon-affecting flows as simulation-only. See `docs/credentials_followup.md` for exact steps to retrieve keys/IDs and complete live smoke after the fact.

Next Steps
- Create governance data model migrations and seed policy rules.
- Implement observe-only Policy/Risk, Arbitrator SIMULATION, Contract Monitor page-only.
- Add governance dashboard pages and Sheets echoes.

## Next Steps
- Implement real channel/supplier adapters in `packages/connectors/`
- Flesh out pricing engine in `packages/pricing/`
- Add DB models + Alembic migrations under `ops/`
- Expand console pages for guardrails and KPIs

## Environment Variables

Set the following variables for integrations and tooling. Some endpoints will still respond in DRYRUN/SANDBOX without these, but full functionality requires them.

Notes on compatibility and fallbacks:
- S3 credentials can be provided as either `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY` or standard AWS envs `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`. Region can be `S3_REGION` or `AWS_DEFAULT_REGION`.
- Google Sheets ledger ID can be provided as `GSHEETS_LEDGER_ID` (preferred) and is accepted as a fallback for `GSHEETS_LEDGER_SPREADSHEET_ID`.
- CJ Dropshipping uses `CJ_API_KEY` which maps internally to an `access_token`.

- `AMAZON_SP_API_CLIENT_ID` – Amazon Selling Partner API client ID
- `AMAZON_SP_API_CLIENT_SECRET` – Amazon SP-API client secret
- `AMAZON_SP_API_REFRESH_TOKEN` – Amazon SP-API refresh token
- `AMAZON_SP_ROLE_ARN` – IAM role ARN for SP-API (if applicable)
- `CJ_API_KEY` – CJ Dropshipping API key
- `GOOGLE_APPLICATION_CREDENTIALS` – Path to Google Service Account JSON (for Sheets)
- `ORDERS_API_KEY` – Orders API key (if applicable)
- `ORDERS_API_SECRET` – Orders API secret (if applicable)
- `ORDERS_REQUIRE_AUTH` – Require authentication for orders endpoints (false by default in dev)
- `ORDERS_AUTH_USERNAME` – Orders API username (if applicable)
- `ORDERS_AUTH_PASSWORD` – Orders API password (if applicable)

Recommended: copy your secrets into a local `.env` and export via your shell or a dotenv loader before running `make verify-integrations`.

### Amazon SP-API Configuration & Health

See the detailed guide at `docs/sp_api_config.md` for obtaining credentials, configuring environment variables, and running safe smokes.

### Post-deploy Observability Smoke (CI)

If you set a GitHub Actions secret `POST_DEPLOY_API_BASE` (e.g. `https://api.example.com`), the pipeline will automatically run `scripts/observability_smoke.sh` against that base URL after deployment. This script warms `/health/integrations` and inspects `/metrics` for `health_check_latency_ms` to verify Prometheus histograms are present.

## Console RBAC & Tokens

Some operator actions in the console (e.g., freeze/unfreeze brains, promote rollouts) require a Bearer token.

1) Get a token from the API (dev quickstart):

```bash
# Create a superuser is handled automatically on API startup using settings.auth.first_superuser* if provided
# Otherwise, register a user (dev only) and login to get a token:
curl -s -X POST http://127.0.0.1:8001/auth/token -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme' | jq .
```

2) Provide the token to the console:

```bash
# Option A: environment for Next.js (before npm run dev)
export NEXT_PUBLIC_API_TOKEN="<paste access_token>"

# Option B: browser local storage (DevTools)
localStorage.setItem('api_token', '<paste access_token>')
```

3) Configure API base (optional):

```bash
export NEXT_PUBLIC_API_BASE="http://127.0.0.1:8001"
```

The console helper at `apps/console/lib/api.ts` automatically includes the Authorization header on requests when a token is present.

### Console Controls: Pause/Resume Pricing

- The Topbar includes a `Pause Pricing` / `Resume Pricing` button (RBAC-protected when auth is enabled).
- This calls `POST /orchestrator/freeze/pricing?freeze=true|false` (see `apps/hive_api/routers/orchestrator.py`).
- When paused, autonomous pricing actions are blocked. Overrides (`/orchestrator/override`) still work.
- Operator feedback is surfaced via toasts; the control reflects the current state using `GET /orchestrator/health`.

## Phase 11 – Compliance & Privacy

Quickstart to validate compliance packs, lint/scanners, and privacy flows.

1) Migrate DB and run API

```bash
make migrate-up
make api-local
```

2) Trigger Policy Pack compile (operator/admin)

```bash
curl -s -X POST http://127.0.0.1:8001/compliance/packs/compile \
  -H 'Content-Type: application/json' \
  -d '{"name":"default","scope":"global","version":"v1","source_uri":"s3://bucket/packs/default.json"}' | jq .
```

3) Pre-publish lint (service/operator/admin)

```bash
curl -s -X POST http://127.0.0.1:8001/compliance/lint/prepublish \
  -H 'Content-Type: application/json' \
  -d '{"listings":[{"listing_ref":"SKU1","channel":"amazon","title":"Widget","description":"Great","images":["https://example.com/i.jpg"],"price_cents":1299,"category_code":"A"}]}' | jq .
```

4) Post-publish scan (operator/admin)

```bash
curl -s -X POST http://127.0.0.1:8001/compliance/scan/postpublish -H 'Content-Type: application/json' -d '{"limit":200}' | jq .
```

5) Inspect results

```bash
curl -s http://127.0.0.1:8001/compliance/violations | jq .
curl -s http://127.0.0.1:8001/compliance/listings/state | jq .
```

6) Privacy (SAR/Erasure)

```bash
# Create SAR request
curl -s -X POST http://127.0.0.1:8001/privacy/requests -H 'Content-Type: application/json' \
  -d '{"rtype":"sar","subject_ref":"user:demo","channel":"api"}' | jq .

# Get SAR artifact
curl -s http://127.0.0.1:8001/privacy/requests/1/artifact | jq .

# Create erasure job
curl -s -X POST http://127.0.0.1:8001/privacy/erasure/jobs -H 'Content-Type: application/json' \
  -d '{"request_id":1,"target":"dtc"}' | jq .

# Get erasure job status
curl -s http://127.0.0.1:8001/privacy/erasure/jobs/1 | jq .
```

Scheduling
- Celery Beat runs `compliance-reload-packs` every 15m and `post-publish-scan` every 10m on `q.backfill`.

Notes
- RBAC enforced on write/operator endpoints. Read-only endpoints are safe in dev.
- Google Sheets echo requires `GOOGLE_APPLICATION_CREDENTIALS` and a configured spreadsheet.

## Console E2E Tests

These Playwright smoke tests verify that key Console pages render and basic accessibility elements are present. They are intentionally lightweight and fast. A broader E2E suite (toasts/refresh + keyboard-only navigation) is being expanded.

### Files
- `apps/console/e2e/playwright.config.ts`
- `apps/console/e2e/tests/health.spec.ts`
- `apps/console/e2e/tests/integrations.spec.ts`
- `apps/console/e2e/tests/finance.spec.ts`
- `apps/console/e2e/tests/pricing.spec.ts`
- `apps/console/e2e/tests/profit.spec.ts`
- `apps/console/e2e/tests/pause_pricing.spec.ts`
- `apps/console/e2e/tests/pricing_csv.spec.ts`

### Run locally
```bash
# Terminal A (Console dev server)
cd apps/console
npm ci
npm run dev    # serves http://localhost:3000 by default

# Terminal B (Playwright install + run)
cd apps/console
npx playwright install
npx playwright test --config e2e/playwright.config.ts

# If Console runs elsewhere
CONSOLE_BASE_URL=http://console-host:3000 npx playwright test --config e2e/playwright.config.ts
```

## Observability Smokes (Local)

Use the lightweight script to validate health probes and optional metrics locally. Histograms are optional in dev and may not appear unless Prometheus client is installed.

```bash
# From repo root
API_BASE=http://127.0.0.1:8001 bash scripts/observability_smoke.sh

# Optional: expose histograms locally
source .venv/bin/activate
pip install prometheus-client
# Restart API so /metrics is mounted
API_BASE=http://127.0.0.1:8001 bash scripts/observability_smoke.sh
```

### Health Slowcheck (Sentry breadcrumbs + latency)

The API provides a synthetic health probe to exercise Sentry breadcrumbs and latency reporting without impacting real probes:

```bash
curl -s "${API_BASE:-http://127.0.0.1:8001}/health/slowcheck?ms=600" | jq .
# Forced failure (returns 500 intentionally, recorded as breadcrumb when Sentry is enabled)
curl -s -o /dev/null -w "%{http_code}\n" "${API_BASE:-http://127.0.0.1:8001}/health/slowcheck?ms=200&fail=true"
```

The observability smoke script (`scripts/observability_smoke.sh`) calls these endpoints and handles the 500 case gracefully.

## Sentry Privacy Posture (Production)

Sentry is configured to protect privacy by default in production:

- `send_default_pii=False`
- `before_send` removes sensitive headers (`authorization`, `cookie`, `set-cookie`, `x-api-key`, etc.), cookies, query strings, and user identifiers (`email`, `username`, `ip_address`, `id`).

This ensures that operational telemetry is captured without leaking sensitive or personal information.

## Redis Health Probe (Config & Fallback)

The Redis check in the Health API prefers the `REDIS_URL` environment variable. If not set, it falls back to the typed settings `settings.redis.url`. When neither is present, the health endpoint reports:

- `configured=false`
- `ok=false` (no attempt is made to ping)

To enable Redis locally:
```bash
export REDIS_URL=redis://127.0.0.1:6379/0
# Restart API, then:
curl -s http://127.0.0.1:8001/health/data | jq '.redis'
