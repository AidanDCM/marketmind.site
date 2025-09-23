# Post-Launch Smoke Checklist

Use this checklist immediately after deploying MarketMind to a live environment.

## Prerequisites
- Database migrated to head
- API reachable at the expected base URL
- Real credentials configured (Amazon SP-API, CJ, Google Sheets)
- RBAC tokens provisioned for operator accounts

## Environment Sanity
- Verify environment is loaded:
  - `GET /_info` returns app metadata
  - `GET /health/summary` returns 200
- Confirm `SIMULATION_ENABLED=false` for live tests

## Orchestrator & Health
- `GET /orchestrator/health` returns 200
- Freeze/unfreeze cycle (RBAC):
  - `POST /orchestrator/freeze/pricing` `{ "freeze": true }` → 200
  - `POST /orchestrator/freeze/pricing` `{ "freeze": false }` → 200

## Ingestion
- `GET /ingest/status` returns checkpoints
- `POST /ingest/run/catalog` → 200 (CJ)
- `POST /ingest/run/signals` → 200
- `POST /ingest/run/orders` → 200 (if configured)

## Pricing
- `GET /pricing/history?asin=<known ASIN>&limit=5` → 200
- `GET /pricing/pending?limit=5` → 200
- `GET /pricing/approved?limit=5` → 200

## Orders (Phase 8)
- `GET /orders/detail/<known id>` → 200
- `POST /orders/reprocess/<known id>` → 200
- `POST /orders/route/<known id>` → 200

## Marketing (Phases 12/14)
- Create a campaign (RBAC): `POST /marketing/campaigns`
- Create an experiment (RBAC): `POST /marketing/experiments`
- Create a variant (RBAC): `POST /marketing/variants`
- Create a bundle (RBAC): `POST /marketing/bundles`
- Verify list endpoints return created items

## Finance (Phase 13)
- `GET /finance/health` → 200
- `GET /finance/ledger/entries` → 200
- Create an invoice (RBAC): `POST /finance/invoices`
- Create a ledger batch/entry (RBAC): `POST /finance/ledger/batches`, `POST /finance/ledger/entries`

## Compliance/Privacy/Tax (Phase 11)
- Pre-publish lint (RBAC): `POST /compliance/lint/prepublish`
- Post-publish scan (RBAC): `POST /compliance/scan/postpublish`
- Privacy SAR create → `POST /privacy/requests`
- Privacy artifact fetch → `GET /privacy/requests/{id}/artifact`
- Erasure job create/fetch → `POST /privacy/erasure/jobs` / `GET /privacy/erasure/jobs/{id}`

## Learning (Phase 15)
- `GET /learning/health` → 200
- Retrain enqueue (RBAC): `POST /learning/models/retrain`
- Historical train (RBAC): `POST /learning/train/historical`
- Verify `/learning/models` and `/learning/metrics` reflect recent runs (DB persistence)

## Profit System
- `GET /profit/log` returns recent entries
- Console `/profit` shows tiles and log; operator forms work with token

## Console RBAC
- Provide token via `NEXT_PUBLIC_API_TOKEN` or `localStorage('api_token')`
- Validate operator actions succeed (200/202)

## Finalization
- Run live helpers:
  - `make live-verify`
  - `make live-all-phases`
- Capture logs (API and workers) for the first 30 minutes post-launch
- Create a CHANGELOG entry for the release
