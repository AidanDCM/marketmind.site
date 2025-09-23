# Live Testing Guide

This guide walks you through running live tests (end-to-end) for the MarketMind platform.

## Prerequisites

- Python venv created and dependencies installed:
  - `infra/docker/requirements-api.txt`
  - `infra/docker/requirements-worker.txt`
  - `requirements-dev.txt`
- Database URL for dev/testing:
  - `export DB_URL=sqlite:///./dev.db`
- Optional: RBAC token for operator actions (freeze/unfreeze, promote rollouts, historical training)

## Start API Locally

```bash
make api-local
# API will bind to http://127.0.0.1:8001
```

Verify basic health:

```bash
curl -s http://127.0.0.1:8001/_info | jq .
curl -s http://127.0.0.1:8001/health/summary | jq .
```

## Run Integrations Verification

```bash
make verify-integrations
```

Expected: All checks PASS (33/33) with warnings for unset external credentials in dev.

## Run Full System Tests (Recommended)

This runs a comprehensive chain: migrate, seed minimal + profit log, verify-integrations, phase backtests (10/12/13/14/15), and API smoke tests.

```bash
make full-system-tests
```

## Profit System Checks

Seed demo rows:

```bash
make seed-profit-log
```

Read profit log:

```bash
curl -s http://127.0.0.1:8001/profit/log | jq .
```

## Learning: Retrain and Historical Train

- Retrain with dataset range (RBAC required):

```bash
# Obtain token
curl -s -X POST http://127.0.0.1:8001/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme' | jq .

# Use token
export API_TOKEN="<paste access_token>"

# Retrain (dataset_range)
curl -s -X POST http://127.0.0.1:8001/learning/models/retrain \
  -H "Authorization: Bearer $API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"brain":"pricing","dataset_range":"2024-01-01..2024-01-31"}' | jq .
```

- Historical training (date range + features):

```bash
# Helper target (uses jq). Provide API_TOKEN for RBAC.
make learning-train-historical BRAIN=pricing START=2024-01-01T00:00:00Z END=2024-01-31T23:59:59Z FEATURES=price,clicks MODEL=auto
```

## Console (Next.js)

Run console in a separate terminal:

```bash
# from apps/console/
export NEXT_PUBLIC_API_URL="http://127.0.0.1:8001"
# optional RBAC for operator actions
export NEXT_PUBLIC_API_TOKEN="<access_token>"

npm install
npm run dev
```

- Visit `/profit` for Profit KPIs, Profit Modules Log, rollouts, and operator actions (promote rollout, historical train)
- Visit `/incidents` for health KPIs and freeze controls
- Visit `/learning` for models, metrics, drift, benchmarks, rollouts, and operator forms (retrain, historical train)

## Launch Checklist

- CI passes end-to-end with hardened gates
- Migrations applied (`make migrate-up`)
- verify-integrations green in the target environment
- RBAC tokens available for operator users
- External credentials configured where applicable (Amazon SP-API, CJ, Google Sheets)

## Troubleshooting

- If `/profit/log` returns Not Found, restart the API (`make api-local`) after updating routers.
- If RBAC endpoints return 401/403, provide a valid token via `Authorization: Bearer <token>`.
- If Celery broker is unavailable, training endpoints still accept requests and return a synthetic task id for dev UX.
