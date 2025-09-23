# Phase 12 — Marketing Automation & Persuasion Engine

This document tracks the implementation and runbook for Phase 12.

## Scope (finalized)
- DB models (SQLAlchemy 2.0 `Mapped[]`/`mapped_column()`):
  - `Campaign`, `CampaignAsset`, `Experiment`, `ExperimentResult`, `CustomerJourney`, `AttributionEvent`
- Alembic migrations:
  - `12ab34cd56ef_phase12_marketing_campaign.py` (campaign)
  - `12ab34cd56f1_phase12_marketing_assets_experiments.py` (assets, experiments)
  - `12ab34cd56f2_phase12_marketing_attribution_journey_results.py` (attribution, journeys, experiment_results)
- API router: `apps/hive_api/routers/marketing.py`
  - `GET/POST /marketing/campaigns`
  - `GET/POST /marketing/assets`
  - `GET/POST /marketing/experiments`
  - `GET/POST /marketing/experiment-results`
  - `GET/POST /marketing/journeys`
  - `GET/POST /marketing/attribution`
- App wiring: `apps/hive_api/main.py` includes `marketing` router under `/marketing`
- RBAC: `SubjectScope` enforcement on all endpoints (dev-friendly optional dependency)
- Makefile targets: `phase12-tests`, `phase12-backtest` (full smoke for all endpoints)

## Usage
1) Start API locally (SQLite):
```
make api-local
```
2) Create a campaign (dev mode allows missing bearer token):
```
curl -sS -X POST "http://127.0.0.1:8001/marketing/campaigns" \
 -H 'Content-Type: application/json' \
 -d '{"name":"Launch Q4","org_id":"org_demo","brain_id":"brain_marketing","status":"draft"}' | python3 -m json.tool
```
3) List campaigns:
```
curl -sS "http://127.0.0.1:8001/marketing/campaigns?org_id=org_demo&brain_id=brain_marketing" | python3 -m json.tool
```

4) Create an experiment and record a result:
```
curl -sS -X POST "http://127.0.0.1:8001/marketing/experiments" \
 -H 'Content-Type: application/json' \
 -d '{"campaign_id":1,"name":"AB Test","kind":"ab","org_id":"org_demo","brain_id":"brain_marketing"}' | python3 -m json.tool

curl -sS -X POST "http://127.0.0.1:8001/marketing/experiment-results" \
 -H 'Content-Type: application/json' \
 -d '{"experiment_id":1,"variant":"A","metric":"ctr","value":0.12,"sample_size":100}' | python3 -m json.tool
```

5) Track attribution and journeys:
```
curl -sS -X POST "http://127.0.0.1:8001/marketing/attribution" \
 -H 'Content-Type: application/json' \
 -d '{"campaign_id":1,"event":"click","source":"google","medium":"cpc","channel":"web","customer_ref":"cust-1"}' | python3 -m json.tool

curl -sS -X POST "http://127.0.0.1:8001/marketing/journeys" \
 -H 'Content-Type: application/json' \
 -d '{"campaign_id":1,"customer_ref":"cust-1","stage":"consideration"}' | python3 -m json.tool
```

## Testing
- Quick smoke: `make phase12-backtest` (migrate → smoke all marketing endpoints)
- Scoped tests: `make phase12-tests` (runs API tests under `apps/hive_api/tests`)
- Current status: PASS
  - Integration tests: 4 passed (apps: marketing create/list for all entities)
  - Coverage: ≥85%
  - Backtests: smoke calls for campaigns, assets, experiments, experiment-results, attribution, journeys

### RBAC in tests/dev
- `get_subject_scope_optional()` returns a permissive `SubjectScope` in dev with brain wildcard `[*]`, allowing API calls without a token.
- In non-dev, a valid bearer token is required and strict org/brain checks are enforced.

## Compliance & Safety
- All create/list endpoints enforce org/brain scope via `SubjectScope.ensure_scope()`.
- Future publish/adapter endpoints will pass Phase 11 lint gates before any side effects.

## Environment
- Reuses existing DB/engine configuration.
- Future flags to expect: `MARKETING_DRYRUN=1` for adapters; Sheets creds reused.

## Rollout Plan
- Shadow mode only (no side effects) until adapters are in place and tested.
- Experiments and attribution in observe-only; analyze results via API.
- Enable publish per channel starting with sandbox/test accounts.

## Verification Matrix
- API: campaigns/assets/experiments/experiment-results/journeys/attribution — PASS (unit + smoke)
- DB: all Phase 12 migrations applied to head — PASS
- Security: RBAC scoped, dev wildcard enabled — PASS (dev), STRICT in prod — PENDING live
- External adapters: DRYRUN only — PENDING (to be added in next increments)
