# Phase B pass 24 — Overview navigation hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** Trend API query contract, lookback validation, health-panel attention navigation  
**Why:** Pass 17 (`2026-06-24-23`) added Overview fetch path contract and parent integration
tests but did not guard trend-summary query params (`attention_only`, `days`, `as_of`),
422 edges for invalid lookback/empty date, `overviewDailyCycle.ts` refetch bundle, or
health-panel "Show attention" wired through the `Overview` parent.

## What changed

| Area | Change |
|---|---|
| `overview_navigation_contract.py` | Trend API path/query params, UI labels, daily-cycle path |
| `tests/test_overview_navigation_contract.py` | +14 tests: 422 edges, lookback matrix, preferences helpers |
| `Overview.test.tsx` | +1 test: health panel Show attention through parent |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 784; stale inventory includes 770 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (784 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `Overview.test.tsx` (+1 test); rely on CI frontend job if `npm` unavailable.

## What could still break

- Secondary-metric CAC vs contribution-profit title overlap — parent test uses last match.
- No Playwright e2e for `localStorage` date persistence across reload.

## Verification checklist

- [x] Trend summary query params documented in client + router
- [x] Invalid `days=0` and empty `as_of=` return 422
- [x] All contract lookback day options accepted by trend-summary API
- [x] `attention_only=true` trend query returns 200 on empty DB
- [x] Overview component documents lookback/attention controls and snapshot Record button
- [x] `overviewPreferences.ts` exports date/stale helpers
- [x] Health panel Show attention opens attention filter through Overview parent
