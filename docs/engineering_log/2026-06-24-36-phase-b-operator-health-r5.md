# Phase B pass 30 — Operator health hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Snapshot-gaps API date scope, readiness empty-date 422, last-cycle empty, preflight `operator_log_exists`, health-panel UI parity  
**Why:** Pass 23 (`2026-06-24-29`) added extended API paths and health-panel date 422 but did not
guard `/operator/snapshot-gaps` date scoping with active experiments, readiness empty `date=`
rejection, checklist-config keys, last-cycle `has_data: false`, preflight `operator_log_exists`
in API responses, desktop health-panel/readiness query params, or `Run cycle now` button wiring.

## What changed

| Area | Change |
|---|---|
| `operator_health_contract.py` | Router path, snapshot-gaps/checklist/last-cycle constants, UI labels, empty-date detail |
| `tests/test_operator_health_contract.py` | +10 tests: API edges, desktop client params, component label parity |
| `OperatorHealthPanel.test.tsx` | +2 tests: `Run cycle now` calls `onRunCycle` (with and without last cycle) |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 884; stale inventory includes 874 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (884 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `OperatorHealthPanel.test.tsx` (+2 tests); rely on CI frontend job if
`npm` unavailable.

## What could still break

- `GET /operator/snapshot-gaps` remains API-only (health panel embeds gaps via `/operator/health-panel`).
- CLI subprocess with pending approval rows not fully contract-tested.
- Empty `date=` on `/operator/snapshot-gaps` is not rejected (only health-panel/readiness/run-cycle).

## Verification checklist

- [x] Router documents strict/date query params and empty-date detail
- [x] Snapshot-gaps API scopes date with active experiment missing snapshot
- [x] Readiness empty `date=` returns 422 with contract detail
- [x] Checklist-config returns min_visits/min_orders/min_spend keys
- [x] Last-cycle empty returns `has_data: false` and `cycle: null`
- [x] Preflight and health-panel preflight include `operator_log_exists`
- [x] Desktop client documents health-panel date and readiness date/strict params
- [x] OperatorHealthPanel documents Run cycle / Record snapshots / Last daily cycle labels
- [x] Preflight summary actions document Open queue and Show attention
- [x] Run cycle now button invokes `onRunCycle` in Vitest
