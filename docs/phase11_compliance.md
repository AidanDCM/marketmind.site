# Phase 11 — Compliance Hardening & Policy Automation

This document tracks Phase 11 scope, implementation details, and quickstarts.

## Scope

- Policy Pack lifecycle: compile -> persist -> hot-reload (Implemented; scheduled every 15m)
- Compliance pre-publish lint (text/image/category/price) (Implemented)
- Post-publish scanners (status/brand gating/term & MAP drift/buybox parity) (Implemented: Enhanced with all scan types)
- Dropshipping guardrails (blind-ship, carrier mapping, supplier whitelist, PO evidence) (Implemented)
- Privacy workflows (SAR export + deletion/erasure jobs + Sheets logging) (INITIAL)
- Tax attestations (writer + exports + Sheets echo) (INITIAL)
- Console & APIs with RBAC and audit logging (Write endpoints enforced)

## Data Model (Alembic `11aa22bb33cc`)

Tables created:
- `compliance_pack`, `restricted_term`, `restricted_category`, `map_catalog`
- `listing_compliance_state`, `compliance_violation`, `listing_snapshot`
- `privacy_request`, `erasure_job`, `tax_attestation`
- `supplier_whitelist`, `carrier_mapping`, `purchase_order_evidence`

## APIs

Routers wired in `apps/hive_api/main.py`:
- `apps/hive_api/routers/compliance.py`
  - `GET /compliance/packs`
  - `POST /compliance/packs:compile` (enqueues compile; Sheets echo)
  - `GET /compliance/violations`
  - `GET /compliance/listing-states`
  - `POST /compliance/lint/prepublish` — trigger pre-publish lint for supplied listings
  - `POST /compliance/scan/postpublish` — trigger post-publish scan (ad-hoc)
  - `POST /compliance/dropship/validate` — validate dropshipping order against guardrails
  - `POST /compliance/suppliers/whitelist` — add/update supplier whitelist entry
  - `GET /compliance/suppliers/whitelist` — list supplier whitelist entries
- `apps/hive_api/routers/privacy.py`
  - `GET /privacy/requests`
  - `POST /privacy/requests`
  - `POST /privacy/erasure/jobs`
  - `GET /privacy/requests/{request_id}/artifact` — retrieve SAR export result URI
  - `GET /privacy/erasure/jobs/{job_id}` — retrieve erasure job state
- `apps/hive_api/routers/tax.py`
  - `GET /tax/attestations`
  - `POST /tax/attestations`

RBAC and audit logging are enforced on compliance/privacy/tax write endpoints.

## Background Jobs

- `apps.hive_worker.tasks.compliance.compile_pack(pack_id, source_uri)` — compiles JSON packs to DB; echoes to Sheets.
- `apps.hive_worker.tasks.compliance.reload_enabled_packs()` — scans all enabled packs and recompiles; safe to run periodically.
- `apps.hive_worker.tasks.privacy.sar_export()` and `run_erasure()` — simulate SAR export and erasure; update DB; Sheets echo.
- `apps.hive_worker.tasks.tax.echo_attestation()` — echoes attestations to Sheets.
- `apps.hive_worker.tasks.lint.pre_publish_lint(listings)` — validates text/image/category/price, returns decisions, echoes to Sheets.
- `apps.hive_worker.tasks.lint.scan_post_publish(limit)` — enhanced post-publish scanners (MAP drift, brand gating, restricted terms, buybox parity) and Sheets echo.
- `apps.hive_worker.tasks.lint.validate_dropship_order(order_id, supplier_id)` — validates dropshipping orders against guardrails.

## Scheduling

- Celery Beat (`apps/hive_worker/celery_app.py`): `compliance-reload-packs` runs every 15 minutes on `q.backfill`.
- Celery Beat: `post-publish-scan` runs every 10 minutes on `q.backfill`.

## Lint & Scanner Usage (dev)

```python
from apps.hive_worker.celery_app import app as celery

# Pre-publish lint
celery.send_task(
    "apps.hive_worker.tasks.lint.pre_publish_lint",
    args=[[{"listing_ref":"SKU1","channel":"amazon","title":"T","description":"D","images":["u"],"price_cents":1000,"category_code":"A"}]],
    queue="q.backfill",
)

# Post-publish scan
celery.send_task("apps.hive_worker.tasks.lint.scan_post_publish", args=[200], queue="q.backfill")
```

### Operator API Usage

```bash
# Pre-publish lint via API
curl -s -X POST http://127.0.0.1:8001/compliance/lint/prepublish \
  -H 'Content-Type: application/json' \
  -d '{"listings":[{"listing_ref":"SKU1","channel":"amazon","title":"T","description":"D","images":["u"],"price_cents":1000,"category_code":"A"}]}' | jq .

# Post-publish scan via API
curl -s -X POST http://127.0.0.1:8001/compliance/scan/postpublish \
  -H 'Content-Type: application/json' \
  -d '{"limit":200}' | jq .

# Dropship validation via API
curl -s -X POST http://127.0.0.1:8001/compliance/dropship/validate \
  -H 'Content-Type: application/json' \
  -d '{"order_id":"ORD123","supplier_id":456}' | jq .

# Add supplier to whitelist
curl -s -X POST http://127.0.0.1:8001/compliance/suppliers/whitelist \
  -H 'Content-Type: application/json' \
  -d '{"supplier_id":456,"supplier_name":"TrustedSupplier","status":"approved","risk_score":10}' | jq .
```

## Quickstart

1. Migrate DB

```bash
make migrate-up
```

2. Run API locally

```bash
make api-local
```

3. Sample calls

```bash
# List packs
curl -s http://127.0.0.1:8001/compliance/packs | jq .

# Create a privacy request
curl -s -X POST http://127.0.0.1:8001/privacy/requests \
  -H 'Content-Type: application/json' \
  -d '{"rtype":"sar","subject_ref":"user:demo","channel":"api"}' | jq .

# Create a tax attestation
curl -s -X POST http://127.0.0.1:8001/tax/attestations \
  -H 'Content-Type: application/json' \
  -d '{"period":"2025-08","jurisdiction":"US-CA","model":"nexus_v1","total_tax_cents":1234,"attester":"ops@example.com"}' | jq .
```

## Next Steps

- Extend scanners: brand gating, restricted term drift, buybox parity.
- Add console widgets for violations and listing states.
- Dropshipping guardrails & evidence retention.
- Expand tests: contract/integration/perf/security for compliance flows.
