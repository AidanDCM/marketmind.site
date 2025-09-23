# MarketMind Developer Glossary

This glossary helps developers quickly navigate core concepts, components, and configuration used across the MarketMind system. For secrets, see `docs/secrets_runbook.md` and `.env.example`.

## Systems & Domains
- __Hive API__ (`apps/hive_api/`): FastAPI service exposing REST endpoints across domains (learning, finance, marketing, pricing, compliance, orders).
- __Hive Worker__ (`apps/hive_worker/`): Celery worker executing background tasks (learning, linting, ingestion, rollouts, benchmarks).
- __Database Models__ (`packages/database/models/`): SQLAlchemy 2.0 models with Alembic migrations.
- __Shared Lib__ (`packages/shared/`): Adapters, config, health probes, sheets, SP-API helpers, secrets rotation, and utilities.

## Key Domains
- __Learning (Phase 15)__: Feature store, model versions/metrics, drift detection, rollouts (shadow/canary/prod), benchmarks.
- __Finance (Phase 13)__: Ledger entries/batches, invoices, reconciliation, forecasts.
- __Marketing (Phase 12/14)__: Campaign assets, experiments, attribution, journeys.
- __Compliance (Phase 11)__: Pre-/post-publish lint, restricted terms, MAP drift, brand gating, privacy & tax workflows.
- __Orders (Phase 8)__: Intake, routing, PO generation (stubs in dev), KPIs, exceptions.
- __Pricing__: Snapshots, history, approvals, brain freeze/unfreeze.

## Endpoints (selected)
- __Learning__ (`/learning/*`): `health`, `models`, `metrics`, `drift`, `benchmarks`, `rollouts`, `models/retrain`.
- __Finance__ (`/finance/*`): `health`, `ledger/entries`, `ledger/batches`, `invoices`, `recon/tasks`, `forecast`.
- __Marketing__ (`/marketing/*`): `assets`, `experiments`, `experiment-results`, `attribution`, `journeys`.
- __Compliance__ (`/compliance/*`): `lint/prepublish`, `scan/postpublish`, `dropship/validate`, supplier whitelist.

## Tasks (selected Celery)
- __Learning__: `train_model`, `detect_drift`, `run_benchmark`, `promote_rollout_task`, `schedule_retrains`.
- __Compliance__: `pre_publish_lint`, `scan_post_publish`, `validate_dropship_order`.

## External Integrations
- __Amazon SP-API__: LWA client, refresh token, IAM role, marketplace IDs. See `.env.example` (AMAZON_SP_API_* vars).
- __CJ Dropshipping__: `CJ_API_KEY`, optionally `CJ_WEBSITE_ID`.
- __Google Sheets__: `GOOGLE_APPLICATION_CREDENTIALS` (service account JSON), `SHEETS_GOVERNANCE_SPREADSHEET_ID`, `GSHEETS_LEDGER_ID`.
- __eBay (Sandbox/Live)__: `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID`, `EBAY_USER_TOKEN`.

## Environment Variables (pointers)
- See `.env.example` for names and comments.
- See `docs/secrets_runbook.md#environment-variables-glossary` for descriptions.
- Never commit secrets. Use `.env` locally or a secret manager in production.

## Marketplace IDs (common)
- US: `ATVPDKIKX0DER`
- CA: `A2EUQ1WTGCTBG2`
- MX: `A1AM78C64UM0Y8`
- UK: `A1F83G8C2ARO7P`
- DE: `A1PA6795UKMFR9`
- FR: `A13V1IB3VIYZZH`
- IT: `APJ6JRA9NG5V4`
- ES: `A1RKKUPIHCS9HS`
- JP: `A1VC38T7YXB528`

## Configuration & Security
- __JWT/Auth__: `SECRET_KEY` (with fallbacks in `apps/hive_api/security.py`), RBAC via `SubjectScope.require_role()`.
- __Flags__: `SIMULATION_ENABLED`, `PRICING_ENABLED`, `INGESTION_ENABLED`, `ORDERS_ENABLED`.
- __Secrets__: Rotate using `packages/shared/secrets/rotate.py`. See `docs/secrets_runbook.md`.

## Secrets Storage & Labels
- __Where secrets live__:
  - Local development: `.env` (untracked). Optionally keep profiles: `.env.sbx` (sandbox), `.env.live` (production-like). Load one at a time.
  - Production/staging: AWS Secrets Manager (see `docs/secrets_runbook.md`).
- __Do not commit secrets__ to the repo. Only `.env.example` contains placeholders.
- __Templates__: Use `.env.sbx.example` (sandbox) and `.env.live.example` (production-like) as starting points. Copy one to `.env` locally and fill in values.
- __Labeling convention__ (use variable names exactly as in `.env.example`):
  - Amazon SP-API (Sandbox): `AMAZON_MODE=SANDBOX` with `AMAZON_SP_API_CLIENT_ID`, `AMAZON_SP_API_CLIENT_SECRET`, `AMAZON_SP_API_REFRESH_TOKEN`, `AMAZON_SP_API_ROLE_ARN`, `AMAZON_SP_API_REGION`, `AMAZON_SP_API_MARKETPLACE_IDS`.
  - Amazon SP-API (Live): `AMAZON_MODE=LIVE` with the Live client id/secret/refresh token; same env names.
  - CJ Dropshipping: `CJ_API_KEY`, optional `CJ_WEBSITE_ID`.
  - Google Sheets: `GOOGLE_APPLICATION_CREDENTIALS` (absolute file path), optional `SHEETS_GOVERNANCE_SPREADSHEET_ID`, `GSHEETS_LEDGER_ID`.
  - eBay Sandbox: `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID`, `EBAY_USER_TOKEN`, `EBAY_MODE=SANDBOX`.
- __How they are loaded__:
  - App and scripts read env via Pydantic settings and `packages/shared/config` loader. `make verify-integrations` and `make adapters-health` rely on the active environment.
- __Rotation & auditing__:
  - Use `packages/shared/secrets/rotate.py` for Amazon/eBay/DB rotations.
  - Document rotations in `docs/secrets_runbook.md` and set AWS Secrets Manager rotation in prod.

## Operations & Makefile Targets (selected)
- __Health__: `make health-summary`, `make adapters-health`.
- __Verification__: `make verify-integrations`, `make phase12-backtest`, `make phase13-backtest`, `make phase14-backtest`, `make phase15-backtest`.
- __Quality__: `make lint`, `make type-check`, `make security-check`.

## Testing
- Unit and integration tests under `apps/hive_api/tests/` and `packages/shared/tests/`.
- Coverage artifacts may be written under `htmlcov/`.

## Documentation (selected)
- `docs/phase15_learning.md` — Learning system and verification.
- `docs/phase13_finance.md` — Finance system.
- `docs/phase11_compliance.md` — Compliance, privacy, tax.
- `docs/secrets_runbook.md` — Secrets management and env glossary.
- `CHANGELOG.md` — Phase entries and verification logs.
