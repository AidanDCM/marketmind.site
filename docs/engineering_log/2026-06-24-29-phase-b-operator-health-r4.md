# Phase B pass 23 — Operator health hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** Extended operator API paths, readiness date query, Gmail secret warning matrix  
**Why:** Pass 16 (`2026-06-24-22`) added contract formatters and core API smoke but did not
cover `/operator/integrations` in the contract, readiness `date=` scoping, Gmail
`live_missing_secret` warning path, desktop client path parity for extended endpoints,
or pending-approval blocker links in the health panel preflight list.

## What changed

| Area | Change |
|---|---|
| `operator_health_contract.py` | Desktop/extended API paths, query params, banner labels |
| `tests/test_operator_health_contract.py` | +13 tests: integrations, date readiness, Gmail secret, 422 |
| `OperatorHealthPanel.test.tsx` | Pending blocker list links to approval queue |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 770; stale inventory includes 757 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (770 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `OperatorHealthPanel.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- `/operator/snapshot-gaps` exists on API but is not yet wired in desktop `client.ts`.
- Dynamic snapshot-gap ID lists beyond truncation only tested via regex group 3.
- Live readiness CLI against operator DB path not subprocess-tested with pending rows.

## Verification checklist

- [x] Desktop client documents core + desktop operator API paths
- [x] Contract formatters match readiness banner regex patterns
- [x] Extended operator endpoints return 200 on empty DB
- [x] Health panel includes integrations snapshot
- [x] Readiness `date=` query scopes snapshot-gap warnings
- [x] Gmail secret warning when live_writes + live mode without `GMAIL_CLIENT_SECRET`
- [x] Empty `date=` query returns 422 on health-panel
- [x] Pending approval blocker in preflight list opens approval queue in UI
