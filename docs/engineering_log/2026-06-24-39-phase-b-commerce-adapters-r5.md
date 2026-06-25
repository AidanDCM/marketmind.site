# Phase B pass 33 — Commerce adapters hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Import batch 404, readiness commerce keys, Shopify products pull, ad CSV wiring  
**Why:** Pass 26 (`2026-06-24-32`) added import/ad path contract, integration key whitelists,
and LiveData Pull Now Vitest but did not guard import batch 404 detail, `getImportBatch` /
history `source` query in desktop client, readiness `commerce` nested keys, Shopify products
pull safe-fail 409, canonical env tuple imports in `commerce_integrations.py`, or Import CSV
button wiring through `importAdCsv`.

## What changed

| Area | Change |
|---|---|
| `commerce_adapters_contract.py` | Batch-not-found detail, readiness commerce key, products label, source query |
| `tests/test_commerce_adapters_contract.py` | +7 tests: 404/409 edges, client parity, readiness commerce keys |
| `LiveData.test.tsx` | +1 test: Import CSV calls `importAdCsv` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 910; stale inventory includes 903 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (910 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `LiveData.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Gmail refresh tokens still not in `_SECRET_PATTERN` — never log them.
- Live Stripe execute with `dry_run=False` covered in hardening tests, not contract module.
- Import batch 404 not yet wired in desktop UI (API + client only).

## Verification checklist

- [x] Imports router documents batch-not-found and empty CSV details
- [x] Unknown import batch returns 404 with contract detail
- [x] Desktop client documents `getImportBatch` and history source query
- [x] Readiness `commerce` payload uses Stripe/Shopify contract keys only
- [x] Shopify products import pull safe-fails 409 without credentials
- [x] `commerce_integrations.py` imports canonical env name tuples
- [x] LiveData documents Shopify Products label and `importAdCsv`
- [x] Import history accepts `source` query param
- [x] Ad summary uses contract `has_data` key on empty DB
- [x] Import CSV button calls `importAdCsv` in Vitest
