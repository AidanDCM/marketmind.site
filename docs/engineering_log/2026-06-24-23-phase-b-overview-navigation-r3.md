# Phase B pass 17 — Overview navigation hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Overview API contract + parent-level navigation for metrics/recommendations  
**Why:** Pass 10 (`2026-06-24-16`) left scale-queue, live-data primary metrics, and
recommendation/lessons navigation covered only in child component tests. Rotation 3
adds a Python contract for Overview fetch paths and closes the parent `Overview.tsx`
integration gaps called out in the pass 10 engineering log.

## What changed

| Area | Change |
|---|---|
| `marketmind/overview_navigation_contract.py` | API paths, localStorage keys, lookback options, lifecycle phrase re-exports |
| `tests/test_overview_navigation_contract.py` | 12 tests: desktop client/preferences parity, API 200 smoke, run-cycle POST |
| `desktop/.../Overview.test.tsx` | +7 tests: orders/revenue live data, CAC/contribution profit, scale queue, score product, lessons |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 656 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (656 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `Overview.test.tsx` (+7 tests); rely on CI frontend job if `npm` unavailable.

## What could still break

- Secondary-metric link titles overlap primary CAC (`Open Active Experiments`) — parent test
  clicks the last matching title for contribution profit.
- No Playwright e2e for `localStorage` date persistence across reload.

## Verification checklist

- [x] Overview fetch API paths documented in `api/client.ts` and return 200 on empty DB
- [x] localStorage keys match `overviewPreferences.ts`
- [x] Scale recommendation opens approval queue through `Overview` parent
- [x] Orders/revenue metrics open Live Data through `Overview` parent
- [x] Lessons no-orders line opens Live Data through `Overview` parent
