# Phase 14 — Experiment Engine: MVT, Bundles, and Attribution Extensions

## Overview
Phase 14 extends the marketing experimentation system with:
- Multi-variant experiments (`ExperimentVariant`)
- Offer bundles lifecycle (`BundleTrial`, `BundleResult`)
- Attribution extensions to tag events with experiment and bundle context
- Minimal API surfaces for listing/creating variants and bundles with RBAC

This phase is production-focused: schema, API, migrations, tests/backtests, and documentation.

## Database Schema (SQLAlchemy 2.0)
New/extended models under `packages/database/models/marketing/`:
- `ExperimentVariant`: key, name, params, allocation_weight, status, FK `experiment_id`
- `BundleTrial`: experiment_id, org_id, brain_id, bundle_ref, components, channel, status, guardrail_flags, published_at, retired_at
- `BundleResult`: FK `bundle_trial_id`, metric, value, sample_size, observed_at
- `CustomerCohort`: org_id, brain_id, name, rule, size_estimate, status
- `AttributionEvent` (extended): `experiment_id` (FK), `variant_key` (str), `bundle_trial_id` (FK)

Alembic migration: `alembic/versions/14ab34cd56f4_phase14_experiments_bundles.py`
- Creates tables and indices
- Adds attribution columns and indices
- Provides downgrade path

Apply migrations:
```
make migrate-up
```

## API Endpoints (FastAPI)
Router: `apps/hive_api/routers/marketing.py`
- `GET /marketing/variants?experiment_id=<id>`: List variants (optionally by experiment)
- `POST /marketing/variants`: Create variant
- `GET /marketing/bundles?experiment_id|org_id|brain_id|status=`: List bundles with filters
- `POST /marketing/bundles`: Create bundle trial

RBAC: `SubjectScope.ensure_scope()` is enforced on write; list endpoints also validate org/brain scope when supplied. Dev mode allows optional auth via `get_subject_scope_optional()`.

## Usage Examples
Create experiment (Phase 12):
```
POST /marketing/experiments
{
  "campaign_id": 1,
  "name": "MVT",
  "kind": "abn",
  "org_id": "org_demo",
  "brain_id": "brain_marketing"
}
```

Create variant:
```
POST /marketing/variants
{
  "experiment_id": 1,
  "key": "A",
  "name": "control",
  "allocation_weight": 1.0
}
```

Create bundle trial:
```
POST /marketing/bundles
{
  "experiment_id": 1,
  "bundle_ref": "BUNDLE-001",
  "channel": "shopify",
  "components": "[{\"sku\":\"SKU1\",\"qty\":1,\"price\":19.99}]"
}
```

## Testing & Backtests
Makefile targets:
- `make phase14-tests` — migrates then runs scoped tests (variants/bundles)
- `make phase14-backtest` — migrates then performs smoke POSTs for campaigns, experiments, variants, bundles

General dev:
- `make api-local` — start API on 127.0.0.1:8001

## Notes & Next Steps
- Attribution pipeline should propagate `experiment_id`, `variant_key`, `bundle_trial_id` on relevant writes (integration to be extended during rollout).
- Guardrails (compliance/privacy from Phase 11) must be honored for bundle content before publish/activation.
- Consider adding `PUT/PATCH` endpoints for lifecycle transitions (`draft` → `active` → `retired`).
- Add dashboards for experiment KPIs and bundle performance in a later phase.

## Verification
- Date: 2025-08-23 (local)
- Phase 14 scoped tests: PASS
  - Command: `make phase14-tests`
  - Result: 1 test passed, coverage 87.77% (>=80% threshold)
- Phase 14 backtest: PASS
  - `make phase14-backtest` smokes for campaigns → experiments → variants → bundles succeeded
- Integrations verification: PASS
  - `make verify-integrations` → 26/26 checks passed
- Adapters health: PASS (DRYRUN)
  - `make adapters-health` successful; expected warnings about unset external creds in dev
- Notes: Benign `urllib3 NotOpenSSLWarning` observed (LibreSSL); non-blocking in dev
