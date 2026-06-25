# Phase B pass 18 — Experiment lifecycle hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Lifecycle API contract, report suffix matrix, ActiveExperiments checklist/mistakes  
**Why:** Pass 11 (`2026-06-24-17`) added report phrase contract and API ruling parity but
left pending-lesson formatting inline, refund/ATC suffix coverage thin, and
`ActiveExperiments` checklist/mistakes sections untested at parent integration level.

## What changed

| Area | Change |
|---|---|
| `experiment_lifecycle_contract.py` | `LIFECYCLE_API_PATHS`, pending-lesson formatter + regex pattern |
| `reports.py` | Uses `format_pending_approvals_lesson` |
| `tests/test_experiment_lifecycle_contract.py` | 11 tests: suffix matrix, API paths, evaluate kill, attention rulings |
| `ActiveExperiments.test.tsx` | +3 tests: `scale_requires_approval` filter, checklist, mistakes |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 667 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (667 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ActiveExperiments.test.tsx` (+3 tests); rely on CI frontend job if
`npm` unavailable.

## What could still break

- `scale_requires_approval` ruling requires specific snapshot math — not generated in
  contract API matrix test (filter UI only).
- Product-specific risk strings remain dynamic beyond suffix/prefix contract.

## Verification checklist

- [x] Pending-lesson formatter matches desktop `PENDING_APPROVALS_LESSON` regex
- [x] Refund/ATC risks include contract suffixes from `generate_daily_report`
- [x] Lifecycle API paths return 200 on empty DB
- [x] `/experiment/evaluate` returns `kill` for 800 visits / 0 orders
- [x] ActiveExperiments loads checklist and mistakes when card focused
