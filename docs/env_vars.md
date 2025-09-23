# Environment Variables Reference

This document lists environment variables used across MarketMind, grouped by component. Variables are shown as names only (no values). The live smoke script will auto-load the first existing file from: `.env`, `infra/.env`, `secrets/.env`, `config/.env`.

- Load order in `scripts/live_smoke.sh`: `.env` → `infra/.env` → `secrets/.env` → `config/.env`

## Core Runtime
- DATABASE_URL — SQLAlchemy DB connection string (e.g., Postgres/SQLite).
- APP_TZ — App timezone (default: UTC). Used by Celery scheduling.
- REDIS_URL — Celery broker/backend URL (default dev: redis://127.0.0.1:6379/0).

## Feature Flags
- FLAG_SIMULATION_ENABLED — When `false`, enables live external calls; otherwise simulated.
- ORDERS_REQUIRE_AUTH — `true` to enforce auth on Orders routes; `false` for local testing.

## Amazon SP-API
- AMAZON_SP_API_CLIENT_ID — LWA client ID for SP-API app.
- AMAZON_SP_API_CLIENT_SECRET — LWA client secret for SP-API app.
- AMAZON_SP_API_REFRESH_TOKEN — Refresh token for seller auth.
- AMAZON_SP_API_ROLE_ARN — IAM role for SP-API access.
- AMAZON_SP_API_LWA_APP_ID — (If used) LWA app/client identifier.
- AMAZON_SP_API_LWA_CLIENT_SECRET — (If used) LWA secret.

Note: `apps/hive_api/routers/health.py` checks `AMAZON_SP_REFRESH_TOKEN` (without `_API_`). Prefer the standardized `AMAZON_SP_API_REFRESH_TOKEN`. Consider aligning the health check to the standardized name.

## CJ (Commission Junction)
- CJ_API_KEY — API key for CJ Catalog and POs.
- CJ_INGEST_LIMIT — Optional limit for catalog ingest (default: 200).

## Google
- GOOGLE_APPLICATION_CREDENTIALS — Path to service account JSON used for Sheets.

## Shipping Providers (Orders)
- EASYPOST_API_KEY — API key for EasyPost.
- SHIPPO_API_KEY — API key for Shippo.

## Optional Integrations (Health Probe Visibility)
- EBAY_APP_ID — eBay application ID.
- WALMART_CLIENT_ID — Walmart client ID.
- AUTODS_API_KEY — AutoDS API key.
- KEEPA_API_KEY — Keepa API key.

## Where these are used
- `apps/hive_api/routers/orders.py`
  - `CJPOClient(api_key=os.getenv("CJ_API_KEY"))`
  - `FulfillmentService(easypost_key=os.getenv("EASYPOST_API_KEY"), shippo_key=os.getenv("SHIPPO_API_KEY"))`
  - `ORDERS_REQUIRE_AUTH` toggles auth requirement
- `apps/hive_api/routers/health.py`
  - Environment-driven integration presence checks (includes `CJ_API_KEY`, `AMAZON_SP_REFRESH_TOKEN`, `EBAY_APP_ID`, `WALMART_CLIENT_ID`, `AUTODS_API_KEY`, `KEEPA_API_KEY`)
- `apps/hive_worker/celery_app.py`
  - `REDIS_URL`, `APP_TZ`
- `apps/hive_worker/tasks/ingest.py`
  - `CJ_INGEST_LIMIT` for catalog fetch
- `scripts/live_smoke.sh`
  - Requires `FLAG_SIMULATION_ENABLED=false`
  - Uses Amazon SP-API, CJ, and optionally Sheets credentials
- `scripts/setup_db.py` / `scripts/create_db.py`
  - `DATABASE_URL` or `DB_URL` for database creation during setup

## Guidance for Developers
- Place secrets in `.env` (or one of the supported paths) for local dev. Do not commit real secrets.
- For live external smoke tests:
  - Ensure `FLAG_SIMULATION_ENABLED=false`
  - Provide Amazon SP-API, CJ, and optionally Google Sheets credentials
  - Run `./scripts/live_smoke.sh` and inspect `reports/smoke/`
- For production, use a secret manager (e.g., AWS Secrets Manager) and environment injection at deploy time.
