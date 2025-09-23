# Release Process (v1.0)

This document defines the simple, auditable release process for MarketMind.

## Prerequisites
- All CI gates green (lint, type-check, tests ≥80% coverage, security scans)
- CHANGELOG.md updated for the release date with verification status
- Go/No-Go Checklist updated (docs/GO_NO_GO.md)

## Versioning
- Semantic versioning: vMAJOR.MINOR.PATCH
- For the initial GA, use v1.0.0

## Steps
1. Bump version (optional)
   - API banner lives in `apps/hive_api/main.py` → `version="..."`
   - Optionally bump any UI version badge if present

2. Commit changes
```bash
git add -A
git commit -m "chore(release): prepare v1.0.0"
```

3. Tag release
```bash
git tag -a v1.0.0 -m "MarketMind v1.0.0"
git push origin v1.0.0
```

4. Build & publish Docker images (if applicable)
- Ensure your CI is configured to build on tags and push to the registry (GHCR/DockerHub).
- Example local build (adjust registry/org):
```bash
docker build -f infra/docker/hive-api.Dockerfile -t ghcr.io/<org>/marketmind-api:v1.0.0 .
docker build -f infra/docker/hive-worker.Dockerfile -t ghcr.io/<org>/marketmind-worker:v1.0.0 .
# Push
# docker push ghcr.io/<org>/marketmind-api:v1.0.0
# docker push ghcr.io/<org>/marketmind-worker:v1.0.0
```

5. Deploy and run post-deploy smoke
```bash
# Point POST_DEPLOY_API_BASE at the deployed API base URL
API_BASE=https://api.example.com bash scripts/observability_smoke.sh
```

6. Archive artifacts
- Save smoke logs, `/metrics` snapshot, and screenshots (optional) under `reports/release/v1.0.0/`

## Optional: Single-file packaging (dev convenience)
You can bundle the API as a single executable for demos using PyInstaller.

1) Install PyInstaller (in your venv):
```bash
pip install pyinstaller
```

2) Build single-file app:
```bash
pyinstaller --onefile --name marketmind-api apps/hive_api/__main__.py
```

3) Run:
```bash
dist/marketmind-api
# env vars required: DB_URL, APP_ENV, (optional) REDIS_URL, SENTRY_DSN
```

Notes:
- Single-file packaging is not required for production.
- Gunicorn + UvicornWorker containers remain the production standard.

## Live Push Readiness (Amazon)

Before enabling live price updates to Amazon, complete the following checklist:

1. Environment Variables (required)
   - `AMAZON_SP_API_CLIENT_ID`
   - `AMAZON_SP_API_CLIENT_SECRET`
   - `AMAZON_SP_API_REFRESH_TOKEN`
   - `AMAZON_SP_API_REGION` (e.g., `NA` | `EU` | `FE`)
   - `AMAZON_SP_MARKETPLACE_ID` (e.g., `ATVPDKIKX0DER` for US)
   - `AMAZON_SP_SELLER_ID`
   - Set `SIMULATION_ENABLED=false` for real external calls

2. Safety Guardrails (server-side enforced)
   - `MAX_PRICE_DELTA_PCT` (default 20) — rejects pushes with absolute delta above this percent vs last price
   - `BRAND_DENYLIST` (comma-separated, optional) — blocks pushes for listed brands
   - Pricing margin floor enforced based on configured guardrails and supplier cost

3a. Guardrails Preview (recommended)
```bash
curl -s "$API_BASE/pricing/guardrails/preview?sku=SKU-TEST-1" | jq .
# Response fields:
# - floor_price_by_margin: minimum price to satisfy margin floor (if supplier cost known)
# - last_price: current listing or latest history
# - allowed_band: [min_allowed_by_delta, max_allowed_by_delta] based on MAX_PRICE_DELTA_PCT
# - recommended_min_safe_price: max(floor_price_by_margin, min_allowed_by_delta)
```

3. Dry-Run Validation (no live write)
```bash
curl -s -X POST "$API_BASE/pricing/push/amazon" \
  -H 'Content-Type: application/json' \
  -d '{"sku":"SKU-TEST-1","dry_run":true}' | jq .
```

4. Live Push (single item)
```bash
curl -s -X POST "$API_BASE/pricing/push/amazon" \
  -H 'Content-Type: application/json' \
  -d '{"asin":"B000TEST01","price":21.99,"currency":"USD"}' | jq .
```

5. Live Push (batch)
```bash
curl -s -X POST "$API_BASE/pricing/push/amazon/batch" \
  -H 'Content-Type: application/json' \
  -d '{"dry_run":false,"items":[{"sku":"SKU1","price":19.99},{"asin":"B08N5WRWNW","price":24.49}]}' | jq .
```

6. Observability & Logs
   - Confirm `/health/summary` is healthy
   - Inspect Sentry (optional) for breadcrumbs and errors
   - Verify `/metrics` exposure in production

