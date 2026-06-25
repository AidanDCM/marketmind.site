# Phase B pass 36 — Approval gate hardening (rotation 6)

**When:** 2026-06-24 (UTC)  
**Theme:** Approve/deny 404 edges, cross-transition 409, status badge map SSOT, Deny Vitest  
**Why:** Pass 29 (`2026-06-24-35`) guarded CRUD and double-transition 409s but did not
assert approve/deny 404 detail fragments, cross-status transition conflicts (denied→approve,
approved→deny), execution-router not-found parity, desktop `denyRecord` client wiring, or
`ApprovalQueue` status badge class map as contract SSOT.

## What changed

| Area | Change |
|---|---|
| `approval_gate_contract.py` | Note body key, path suffixes, `GATE_STATUS_BADGE_CLASSES` |
| `tests/test_approval_gate_contract.py` | +9 tests: 404 edges, cross-transition 409, badge parity |
| `ApprovalQueue.test.tsx` | +1 test: Deny calls `denyRecord` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 944; pass 36; stale inventory includes 935 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (944 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ApprovalQueue.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Batch `POST /execute` remains API-only (no desktop control).
- New approval statuses need UI badge map + contract updates.
- Filter label `auto allowed` is runtime `replace("_", " ")` — contract guards transform.

## Verification checklist

- [x] Approve/deny unknown IDs return 404 with not-found fragment
- [x] Denied→approve and approved→deny return 409 transition conflict
- [x] Empty approvals list returns `[]`
- [x] Execute 404 includes not-found fragment
- [x] Approvals router documents note body and path suffixes
- [x] Desktop client documents `denyRecord` with note payload
- [x] ApprovalQueue badge map matches `GATE_STATUS_BADGE_CLASSES`
- [x] Execution router documents 404 not-found pattern
- [x] Deny button calls `denyRecord` with empty note default
