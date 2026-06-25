# Phase B pass 26 — Commerce adapters hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** Import/ad API path contract, Stripe/Shopify integration key whitelists, LiveData UI  
**Why:** Pass 19 (`2026-06-24-25`) added handler/policy matrix and Shopify execute dry-run
but did not guard import history/ad endpoints, Stripe/Shopify integration JSON key
whitelists, Shopify source 409 safe-fail paths, ad CSV empty-body 422, `SECRET_MASK_VECTORS`
in the contract test module, or LiveData Pull Now desktop wiring.

## What changed

| Area | Change |
|---|---|
| `commerce_adapters_contract.py` | Import history/ad paths, integration keys, LiveData labels |
| `tests/test_commerce_adapters_contract.py` | +19 tests: 409/422 edges, mask vectors, router parity |
| `LiveData.test.tsx` | +1 test: Pull Now triggers Stripe import |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 819; `MIN_VITEST_FILES` → 29 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (819 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `LiveData.test.tsx` (+1 file, +1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Gmail refresh tokens still not in `_SECRET_PATTERN` — never log them.
- Live Stripe execute with `dry_run=False` covered in hardening tests, not contract module.
- Import batch 404 not exercised from desktop yet.

## Verification checklist

- [x] Stripe/Shopify integration payloads expose contract keys only
- [x] `/operator/integrations` includes `live_writes.enabled`
- [x] Desktop client documents import history and ad import paths
- [x] Sources/imports routers document contract path suffixes
- [x] Shopify source + import pull Stripe safe-fail 409 without credentials
- [x] Empty ad CSV returns 422 with contract detail string
- [x] Ad summary empty DB returns `has_data: false`
- [x] `SECRET_MASK_VECTORS` each redacted by `mask_secret`
- [x] LiveData component documents source labels and 409 hint
- [x] Pull Now calls `pullAndSaveStripeOrders`
