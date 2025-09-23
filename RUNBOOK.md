# MarketMind Production Runbook (v1.0)

## Deploy
- CI: build -> test -> scan -> migrate -> deploy -> smoke
- Rollback: redeploy previous image tag; revert DB if needed

## Health / Probes
- Liveness: /health/summary
- Readiness: /health/data  
- Metrics: /metrics (Prometheus)

## Common Incidents
- API 5xx spike: check Sentry; check DB/Redis health; scale API
- Worker lag: check Celery queue depth; scale workers; inspect failing tasks
- Auth errors: rate limit events; verify Redis; check JWT signing keys

## Scaling
```bash
# Scale API
docker-compose up -d --scale api=3
kubectl scale deployment marketmind-api --replicas=3

# Scale workers  
docker-compose up -d --scale worker=5
kubectl scale deployment marketmind-worker --replicas=5
```

## Health Checks
```bash
# API health
curl https://api.marketmind.ai/health/summary

# Worker status
celery -A apps.hive_worker.celery_app.app inspect ping

# Queue depth
redis-cli -u $REDIS_URL llen celery
```

## On-Call
- Escalation policy: see ONCALL.md
- Dashboards: Grafana, Sentry project
- Contact: oncall@marketmind.ai

## Restore Drill Log (Disaster Recovery Evidence)

Run a scratch restore using the provided scripts, then record the evidence below. Perform this at least once before GA and quarterly thereafter.

Commands:
```bash
DB_URL=postgres://prod ./scripts/db/backup.sh
# note the generated file name: backup-YYYYMMDD-HHMMSS.sql

SRC_SQL=backup-YYYYMMDD-HHMMSS.sql \
TARGET_DB_URL=postgres://scratch-db-url \
./scripts/db/restore.sh
```

Receipt:
- When: 2025-09-19T18:42Z
- Operator: <name>
- Source: backup-YYYYMMDD-HHMMSS.sql
- Target: postgres://scratch-db-url
- Result: ✅ success (validated core tables present)

---

## Observability Smokes (Post-Deploy)

Use the lightweight smoke script to validate health probes and optional metrics:

```bash
API_BASE=https://api.example.com bash scripts/observability_smoke.sh
```

Checks performed:
- Warms `/health/integrations` (repeated) to exercise probes
- Inspects `/metrics` for `health_check_latency_ms` (Prometheus histograms)
- Confirms `/health/summary` is healthy

Synthetic latency and breadcrumb check:
- `GET /health/slowcheck?ms=600` — adds Sentry breadcrumb (if enabled), returns `{ ok: true, duration_ms }`
- `GET /health/slowcheck?ms=200&fail=true` — returns HTTP 500 intentionally; used to validate error tracking without harming real probes

Notes:
- Histograms are optional; if the Prometheus client is not installed or histograms are disabled, this step reports as informational but does not fail.
- In CI, set `POST_DEPLOY_API_BASE` secret to run this automatically after deploy.

## Amazon Price Push (Operator)

Use these steps to safely update listing prices on Amazon via SP‑API.

Prerequisites:
- Environment variables set (no secrets in code):
  - `AMAZON_SP_API_CLIENT_ID`, `AMAZON_SP_API_CLIENT_SECRET`, `AMAZON_SP_API_REFRESH_TOKEN`
  - `AMAZON_SP_API_REGION` (NA|EU|FE), `AMAZON_SP_MARKETPLACE_ID`, `AMAZON_SP_SELLER_ID`
  - `SIMULATION_ENABLED=false` for live calls
- Optional safety toggles:
  - `MAX_PRICE_DELTA_PCT` (default 20)
  - `BRAND_DENYLIST` (comma-separated)

Endpoints:
- Single: `POST /pricing/push/amazon`
- Batch:  `POST /pricing/push/amazon/batch`

Dry-run (no write):
```bash
curl -s -X POST "$API_BASE/pricing/push/amazon" \
  -H 'Content-Type: application/json' \
  -d '{"sku":"SKU-TEST-1","dry_run":true}' | jq .
```

Live push (single):
```bash
curl -s -X POST "$API_BASE/pricing/push/amazon" \
  -H 'Content-Type: application/json' \
  -d '{"asin":"B000TEST01","price":21.99,"currency":"USD"}' | jq .
```

Live push (batch):
```bash
curl -s -X POST "$API_BASE/pricing/push/amazon/batch" \
  -H 'Content-Type: application/json' \
  -d '{"dry_run":false,"items":[{"sku":"SKU1","price":19.99},{"asin":"B08N5WRWNW","price":24.49}]}' | jq .
```

Guardrails (server-side):
- Margin floor enforced using supplier cost; below floor → `400 below_min_margin`.
- Max delta vs last price; above `MAX_PRICE_DELTA_PCT` → `400 max_delta_exceeded`.
- Brand denylist blocks writes → `403 brand_denied`.

Rollback:
- Re‑push last known good price using the same endpoint with previous value.
- DB updates (ChannelListing + PriceHistory) are logged for audit.

Troubleshooting:
- `503 Missing AMAZON_SP_SELLER_ID` → set required env.
- `503 LWA token error` → verify Client ID/Secret/Refresh token and region.
- `400 below_min_margin` → increase price or adjust cost/fees guardrails if appropriate.
- Inspect Sentry breadcrumbs (optional) and `/metrics` for anomalies.

## Sentry (Production Privacy)

Sentry is configured to avoid PII by default:

- `send_default_pii=False`
- `before_send` redacts sensitive headers (e.g., `authorization`, `cookie`, `set-cookie`, `x-api-key`), cookies, query strings, and user identifiers (`email`, `username`, `ip_address`, `id`).

To validate:
- Trigger a safe write flow (e.g., `POST /pricing/snapshot` with a dev token) and confirm breadcrumbs/events appear in Sentry without PII.

## OpenTelemetry (APM)

Set the following for production to ship spans to your APM backend:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-collector.example.com
export OTEL_RESOURCE_ATTRIBUTES=service.name=hive-api,service.version=prod
```

Validate:
- Trigger an end-to-end flow (API → Worker) and confirm spans are visible and properly linked.

## Prometheus (Metrics)

The API mounts `/metrics` automatically when `prometheus_client` is installed. Histograms and counters are emitted by health probes and selected tasks.

Local enablement:
```bash
source .venv/bin/activate
pip install prometheus-client
# restart API; verify:
curl -s http://127.0.0.1:8001/metrics | grep health_check_latency_ms || true
```

## Redis Health Probe Guidance

The Redis probe prefers `REDIS_URL` and falls back to `settings.redis.url`. When neither is set, `/health/data` reports `configured=false`.

To enable in dev:
```bash
export REDIS_URL=redis://127.0.0.1:6379/0
# restart API; verify:
curl -s http://127.0.0.1:8001/health/data | jq '.redis'
```

## Console E2E Smokes (Playwright)

These smokes validate that core Console pages render and basic A11y hints exist. A broader suite (toasts/refresh + keyboard-only navigation) is being expanded.

Run:
```bash
# Terminal A: run Console
cd apps/console
npm ci
npm run dev    # http://localhost:3000

# Terminal B: install browsers + run tests
cd apps/console
npx playwright install
npx playwright test --config e2e/playwright.config.ts

# If Console is hosted elsewhere
CONSOLE_BASE_URL=https://console.example.com npx playwright test --config e2e/playwright.config.ts
```

Troubleshooting:
- Ensure the Console server is running and reachable from the test runner.
- If TypeScript typings are missing, run `npm ci` before executing Playwright.
