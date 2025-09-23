# Phase 7 Testing & Backtesting Plan

This plan validates multi‑brain orchestration, global scaling, autonomy controls, and enterprise‑grade resilience.

## Scope
- Unit tests per brain (pricing/marketing/analytics/compliance/expansion)
- Shared bus reliability (Redis Streams or Kafka optional)
- Integration across brains (end‑to‑end order and pricing flows)
- Load and chaos tests (10k orders/hour across regions)
- Backtesting on historical dataset (6‑month replay)
- Security (keys leakage, RBAC, orchestrator/dashboard surface)

## Unit Tests
- Pricing: undercut logic, guardrails, tax‑inclusive targets
- Marketing: copy generation variants, A/B assignment, KPI logging
- Analytics: KPI aggregation, retention windows, anomaly detection hooks
- Compliance: jurisdiction checks, tax computation, fraud flags
- Expansion: market suitability scoring, supplier selection heuristics

## Shared Memory Bus
- Publish/consume loops for topics `kpi.*`, `decision.*`, `insight.share`
- Idempotency: ensure message keys dedupe; checkpoints upsert to `IngestCheckpoint`
- Backpressure: verify consumer lag under load; autoscaling guidance

## Integration Tests
- Pipeline: pricing → supplier → tax → marketing
- Decision logging: SQL + Google Sheets append in DRYRUN
- Overrides: simulate admin freeze/override and verify effects

### Orchestrator Verification (added)
- `GET /orchestrator/health` returns 200 and freeze states map
- `GET /orchestrator/queues` lists declared Celery task names
- `POST /orchestrator/freeze/{brain}?freeze=true` returns 200, then `freeze=false` to unfreeze
- `POST /orchestrator/override?...` accepts override (200)
- Automated: `make verify-integrations` runs these checks

## Load Tests
- Locust plan in `locustfile.py` (already present)
- Make target `make load-test` parameters:
  - USERS (default 500)
  - SPAWN (default 25)
  - DURATION (default 600)
- KPIs: error rate < 1%, P95 latency < 300ms for read endpoints, no data loss

### Running locally
- Install Locust once:
  ```bash
  pip install locust
  ```
- Short sanity run:
  ```bash
  make load-test USERS=100 SPAWN=10 DURATION=120
  ```
  Review console output for request failures and latency percentiles.

## Backtesting
- Replay historical catalog and pricing snapshots through brains
- Compare alternate decisions vs. baseline ROI; require uplift ≥ X% (configurable)
- Store results in SQL + export to Sheets for audit

### Decision Ledger Audit
- Assert that brain stubs append `DecisionLog` rows on successful runs
- Spot-check fields: `brain`, `decision_id` (if provided), `context`, `decision`, `created_at`

## Security
- Simulate leaked API keys; ensure detectors fire and rotate procedures documented
- Pen‑test orchestrator & dashboard endpoints (authz, rate limiting, CSRF where applicable)

## Phase 7 Backtest Entry Point
- `make phase7-backtest` runs:
  - DB migrate → integration verification (`make verify-integrations`)
  - Load test (short) → summary KPIs
  - Summarizes results to console; future: append to CHANGELOG automatically

### Alembic note (dev)
- If you created tables manually or ran migrations previously, you may need to stamp Alembic to head to avoid duplicate table errors:
  ```bash
  DB_URL=sqlite:///./dev.db PYTHONPATH=. .venv/bin/python scripts/alembic_cli.py -c alembic.ini stamp head
  ```

### Dev environment skip behavior
- In dev/CI without a Celery broker or when certain modules are disabled, ingestion endpoints return HTTP 200 with a `status: "skipped"` payload so end‑to‑end verification can proceed without side effects:
  - `POST /ingest/run/catalog` → `{ "status": "skipped", "reason": "celery_unavailable" }`
  - `POST /ingest/run/orders` → `{ "status": "skipped", "reason": "orders_disabled" }` or `{ "reason": "celery_unavailable" }`
  - `POST /ingest/run/pricing` → returns `{ "status": "skipped", "reason": "spapi_not_configured" }` when Amazon SP‑API creds are missing.

### Final Verification (dev)
- On 2025‑08‑20 the following passed on local dev:
  - `make verify-integrations` → 19/19 PASS
  - `make adapters-health` → PASS
  - `make test` → PASS (≥80% coverage on active DB tests)
  - `make phase7-backtest` → verification PASS; short load test requires Locust installed

## Results – 2025‑08‑20 (dev)

- CJ Dropshipping catalog smoke: SUCCESS. Checkpoint written under pipeline `catalog`, source `cj` (see `GET /ingest/status`).
- Amazon SP‑API pricing smoke: TRIGGERED via `/ingest/run/pricing` with sandbox credentials; runs async.
- Simulation flag: set `SIMULATION_ENABLED=false` (env) to enable real external calls. Do not use `FEATURE_SIMULATION_ENABLED`.
- Health endpoints: `/health/data`, `/health/live`, `/health/ready` all stable (HTTP 200 under load).
- Load KPIs (headless, USERS=50, SPAWN=5, DURATION=30):
  - Requests: 1,621 total; Aggregate avg 66 ms; P95 ≈ 250 ms (read endpoints); 0 failures on health endpoints.
  - Test pages for `/products/*` are placeholders and return 404 by design in this build; failures logged accordingly in reports.
- Artifacts:
  - CSV: `reports/load/metrics_stats.csv`, `metrics_stats_history.csv`, `metrics_failures.csv`, `metrics_exceptions.csv`
  - HTML: `reports/load/report.html`

### Operational Notes

- Ensure Celery/Redis are running and API/worker share identical env vars.
- Amazon sandbox pricing does not write an ingest checkpoint by default; success can be verified via logs. Optionally add a checkpoint write in the background task if needed.
