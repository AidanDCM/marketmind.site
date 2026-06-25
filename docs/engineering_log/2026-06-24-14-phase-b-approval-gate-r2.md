# Phase B pass 8 — Approval gate hardening (rotation 2)

**When:** 2026-06-24 (UTC)  
**Theme:** Pending/denied/blocked never execute; dry_run defaults; batch safety  
**Why:** Pass 2 (2026-06-24-08) covered core paths but not every `BLOCKED_ACTIONS`
member, API idempotency, denied status, or execute-all batch behavior when one row is
blocked.

## What changed

| Area | Change |
|---|---|
| `tests/test_approval_gate_hardening.py` | 19 tests: full blocked-action matrix, batch capture, API 409/200 paths |
| `desktop/.../ApprovalQueue.test.tsx` | Denied records hide Execute and Approve |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (540 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ApprovalQueue.test.tsx` (+1 test); rely on CI frontend job locally if
`npm` unavailable.

## What could still break

- UI does not expose `executeAll` — batch execute is API/operator-script only.
- Live Stripe/Shopify/Gmail with credentials still has no end-to-end live-write test
  (intentionally off by default).

## Verification checklist

- [x] Every `BLOCKED_ACTIONS` entry refused by policy and executor
- [x] `POST /execute` returns 409 for denied approvals
- [x] Second execute returns `already_executed` without duplicate ledger event
- [x] `POST /execute` batch returns 200 with per-row refusal for blocked actions
- [x] Denied ApprovalQueue cards show no execute control
