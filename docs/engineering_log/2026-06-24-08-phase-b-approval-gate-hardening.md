# 2026-06-24 — Phase B: Approval gate hardening (pass 2)

## Why

Phase B rotation item 1: **pending approvals never execute; dry_run defaults**. Policy and
executor tests existed but gaps remained:

- No regression for **BLOCKED_ACTIONS** on the executor path (`bypass_approval_gate` with
  APPROVED row).
- No API test that `/execute` batch skips PENDING rows.
- Commerce policy **aliases** and non-approved status variants under-tested.
- Desktop **ApprovalQueue** had zero Vitest — UI hardcodes `executeApproved(id, true)` but
  was unverified.
- API client `executeApproved` default `dry_run=true` not asserted.

## Where

- `tests/test_commerce_approval_policy.py` — aliases, bypass block, status parametrize
- `tests/test_executor.py` — blocked action refusal, default dry_run
- `tests/test_api.py` — blocked 409, execute-all skips pending
- `desktop/src/components/ApprovalQueue.test.tsx` — pending vs approved UI gate
- `desktop/src/api/client.test.ts` — executeApproved default body

## When

2026-06-24 UTC (Phase B pass 2).

## Verification

```text
python -m ruff check .                    -> exit 0
python -m pytest -q                       -> 476 passed
python scripts/local_ci.py                -> PASS
cd desktop && npm test                    -> CI frontend job
```

## Gaps remaining

- Live execution paths (Stripe/Shopify/Gmail with credentials) — covered in adapter tests;
  no end-to-end live-write integration test (intentionally off by default).
- Phase B rotation next: operator health deep pass.
