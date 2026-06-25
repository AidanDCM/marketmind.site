# Phase B pass 29 — Approval gate hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Approval CRUD API contract, transition 409 edges, queue approve wiring  
**Why:** Pass 22 (`2026-06-24-28`) added HIGH_RISK approved matrix and filter-bar parity
but did not guard list/get/pending API paths, status query param, double-approve/deny 409
fragments, execute-all endpoint, denied execute refusal, filter localStorage helpers, or
desktop Approve button wiring through `approveRecord`.

## What changed

| Area | Change |
|---|---|
| `approval_gate_contract.py` | Router paths, UI labels, filter storage, transition fragments |
| `tests/test_approval_gate_contract.py` | +14 tests: CRUD smoke, 409 edges, execute-all, UI parity |
| `ApprovalQueue.test.tsx` | +1 test: Approve calls `approveRecord` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 874; stale inventory includes 860 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (874 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ApprovalQueue.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Filter label `auto allowed` is runtime `replace("_", " ")` — contract guards transform.
- Batch `POST /execute` remains API-only (no desktop control).
- New approval statuses need UI badge map updates.

## Verification checklist

- [x] Approvals/execution routers document contract API paths
- [x] Desktop client documents status query param and pending path
- [x] Pending list excludes approved records
- [x] GET by id returns record; unknown returns 404
- [x] Double approve/deny returns 409 with transition fragment
- [x] Status query filters pending approvals
- [x] Execute-all returns empty list on empty DB
- [x] Denied record execute returns not-approved 409
- [x] ApprovalQueue documents Approve/Deny/Execute buttons and filter transform
- [x] Preferences module exports storage key and filter helpers
- [x] Approve button calls `approveRecord` with empty note default
