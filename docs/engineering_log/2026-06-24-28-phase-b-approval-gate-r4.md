# Phase B pass 22 — Approval gate hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** Approval/execute API path contract, HIGH_RISK approved matrix, queue UI parity  
**Why:** Pass 15 (`2026-06-24-21`) added action-set SSOT and blocked UI state but did not
parametrize HIGH_RISK actions with `approved` policy status, document approval CRUD API
paths in the contract, or test approve/deny/execute-log API flows and filter-bar parity
with `approvalQueuePreferences.ts`.

## What changed

| Area | Change |
|---|---|
| `approval_gate_contract.py` | API paths, filter options, UI status gate constants |
| `tests/test_approval_gate_contract.py` | +29 tests: approved matrix, approve/deny API, execute log |
| `ApprovalQueue.test.tsx` | +2 tests: filter options, `already_executed` execute message |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 757; stale inventory includes 728 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (757 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ApprovalQueue.test.tsx` (+2 tests); rely on CI frontend job if
`npm` unavailable.

## What could still break

- New HIGH_RISK actions must be added to contract or parametrized tests fail.
- UI `executeAll` batch path remains API-only (no desktop control).
- Live commerce writes still off by default.

## Verification checklist

- [x] Every HIGH_RISK action returns Approved when `approval_status=approved`
- [x] Desktop client documents approval/execute paths and dry-run default
- [x] Filter options match `approvalQueuePreferences.ts`
- [x] Approve/deny API transitions pending → approved/denied
- [x] Execute log records `event_id` after dry-run execute
- [x] ApprovalQueue filter bar renders all contract filter options
- [x] Repeat execute surfaces `already_executed` in UI message
