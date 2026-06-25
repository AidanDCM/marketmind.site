# Phase B pass 37 — Operator health hardening (rotation 6)

**When:** 2026-06-24 (UTC)  
**Theme:** Snapshot-gaps empty-date 422, run-cycle 422, pending blocker API/CLI, UI labels  
**Why:** Pass 30 (`2026-06-24-36`) guarded health-panel/readiness empty `date=` but left
`/operator/snapshot-gaps` accepting blank dates, did not test run-cycle empty-date rejection,
integrations subkey parity, readiness/preflight pending-blocker API responses, CLI exit code
with pending approvals on a real sqlite file, or `Snapshots for` gap header in Vitest.

## What changed

| Area | Change |
|---|---|
| `operator.py` | Empty `date=` on snapshot-gaps returns 422 with contract detail |
| `operator_health_contract.py` | Run-cycle/last-cycle paths, integrations subkeys, UI button labels |
| `tests/test_operator_health_contract.py` | +11 tests: 422 edges, pending blocker API/CLI, integrations |
| `OperatorHealthPanel.test.tsx` | +1 test: `Snapshots for` date header when gaps missing |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 955; pass 37; stale inventory includes 944 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (955 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `OperatorHealthPanel.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- `GET /operator/snapshot-gaps` remains unwired in desktop `client.ts` (health panel embeds gaps).
- CLI subprocess uses `DATABASE_URL` file DB — in-memory URLs still not subprocess-testable.
- Run-cycle POST still requires live runner; empty DB smoke only covers 422 date edge.

## Verification checklist

- [x] Snapshot-gaps empty `date=` returns 422 with contract detail
- [x] Run-cycle empty `date=` returns 422 with contract detail
- [x] Router documents empty-date guards on snapshot-gaps and run-cycle
- [x] Desktop client documents run-cycle and last-cycle paths
- [x] Integrations endpoint returns gmail/stripe/shopify keys
- [x] Preflight API reports pending count and contract blocker
- [x] Readiness API not ready when pending approvals exist
- [x] Snapshot-gaps empty DB returns zero missing
- [x] Last-cycle response uses contract `cycle` key
- [x] Health panel documents Import ads / View snapshots / Snapshots for labels
- [x] Readiness CLI exits 1 with pending blocker on file-backed DB
- [x] Vitest shows Snapshots for date header when gaps exist
