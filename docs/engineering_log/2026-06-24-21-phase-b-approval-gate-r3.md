# Phase B pass 15 — Approval gate hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Contract SSOT for action sets; full HIGH_RISK/AUTO/BLOCKED matrix; UI blocked state  
**Why:** Passes 2 and 8 covered core executor/API paths but action frozensets lived only in
`commerce_approval_policy.py`, and not every HIGH_RISK or AUTO_ALLOWED member had an
explicit regression. Rotation 2 docs referenced `approval_gate_contract` before the module
existed.

## What changed

| Area | Change |
|---|---|
| `marketmind/approval_gate_contract.py` | BLOCKED/HIGH_RISK/AUTO_ALLOWED, handler names, refusal fragments |
| `commerce_approval_policy.py` | Imports action sets; uses `APPROVED_STATUS_ALIASES` |
| `executor.py` | Refusal messages wired to contract fragments |
| `tests/test_approval_gate_contract.py` | 45 tests: full action-set matrix + API/executor parity |
| `ApprovalQueue.test.tsx` | Blocked cards show no approve/deny/execute |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 630; stale inventory includes 585 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (630 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ApprovalQueue.test.tsx` (+1 test); rely on CI frontend job if `npm` unavailable.

## What could still break

- New HIGH_RISK actions must be added to `approval_gate_contract.py` or parametrized tests fail.
- Executor handler actions use queue aliases (`scale_campaign`) — contract tests normalize to policy names.
- Live Stripe/Shopify/Gmail writes still have no default-on E2E test.

## Verification checklist

- [x] Policy module re-exports match contract frozensets
- [x] Every HIGH_RISK action returns Needs Review when pending
- [x] Every AUTO_ALLOWED action skips approval gate
- [x] Every BLOCKED action stays blocked with `complete` status
- [x] Pending `POST /execute/{id}` returns 409 with contract refusal fragment
- [x] Blocked ApprovalQueue cards expose no gate controls
