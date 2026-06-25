# Phase B pass 40 — Commerce adapters hardening (rotation 6)

**When:** 2026-06-24 (UTC)  
**Theme:** Shopify orders import pull 409, batch_id/csv_text SSOT, ad summary keys, Shopify Pull Vitest  
**Why:** Pass 33 (`2026-06-24-39`) guarded import batch 404 and Import CSV Vitest but did not
assert `/imports/pull/shopify/orders` 409 without credentials, `batch_id`/`csv_text` keys in
imports router, `fetchAdSpendSummary` / `pullAndSaveStripeOrders` client parity, ad summary
response key SSOT, commerce action alias targets in HIGH_RISK set, LiveData `fetchAdSpendSummary`
wiring, or Shopify Orders tab Pull Now in Vitest.

## What changed

| Area | Change |
|---|---|
| `commerce_adapters_contract.py` | `batch_id`/`csv_text` keys, ad summary response keys, LiveData test path |
| `tests/test_commerce_adapters_contract.py` | +12 tests: Shopify orders pull 409, alias targets, client/router parity |
| `LiveData.test.tsx` | +1 test: Shopify Orders tab calls `pullAndSaveShopifyOrders` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 985; pass 40; stale inventory includes 973 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (985 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `LiveData.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Gmail refresh tokens still not in `_SECRET_PATTERN` — never log them.
- Live Stripe execute with `dry_run=False` covered in hardening tests, not contract module.
- Import batch 404 not yet wired in desktop UI (API + client only).

## Verification checklist

- [x] `/imports/pull/shopify/orders` returns 409 without credentials (secret-free)
- [x] Imports router documents `batch_id` and `csv_text` body key
- [x] Desktop client documents `fetchAdSpendSummary` and `pullAndSaveStripeOrders`
- [x] Ad summary response includes contract `has_data`/`summary` keys
- [x] Commerce action alias targets are HIGH_RISK policy actions
- [x] Imports router documents `source` query param for history
- [x] LiveData component documents `fetchAdSpendSummary`
- [x] LiveData contract test file exists on disk
- [x] Shopify Orders tab Pull Now calls `pullAndSaveShopifyOrders` in Vitest
