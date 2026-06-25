# Phase B pass 7 — Docs drift hardening

**When:** 2026-06-24 (UTC)  
**Theme:** OPERATING_INDEX, OWNER_MANUAL, testing manual, and deployment docs vs code  
**Why:** OWNER_MANUAL still cited `STRIPE_SECRET_KEY`, `SHOPIFY_SHOP_DOMAIN`, "Building
(active slice development)", and 465/13 test counts while the suite had grown to 512 pytest
and 27 Vitest files.

## What changed

| Area | Change |
|---|---|
| `marketmind/docs_contract.py` | Canonical env names + `MIN_PYTEST_CASES` / `MIN_VITEST_FILES` |
| `tests/test_docs_drift.py` | 9 regression tests encoding doc/code parity |
| `OWNER_MANUAL.md` | Hardening status, canonical env table, local_ci / deploy verify tasks |
| `AGENTS.md`, `SLICE_WORKFLOW.md` | 512+ pytest, 27+ Vitest |
| `MARKETMIND_TESTING_AND_EVIDENCE.md` | Inventory, `local_ci --full`, Phase B rotation list |
| `docs/DEPLOYMENT.md` | Post-deploy: both `verify_marketmind_deploy` and readiness API check |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (521 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- `MIN_PYTEST_CASES` / `MIN_VITEST_FILES` must be bumped when the suite grows or CI fails
  on docs drift tests.
- Historical engineering-log entries still mention 465 tests (intentional archive).
- Frontend Vitest count is file-based, not test-case count.

## Verification checklist

- [x] OWNER_MANUAL has no stale Stripe/Shopify env var names
- [x] OPERATING_INDEX cites 512 pytest + 27 Vitest files
- [x] DEPLOYMENT documents both post-deploy verifier scripts
- [x] `tests/test_docs_drift.py` passes against updated docs
