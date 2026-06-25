# Phase B pass 11 — Experiment lifecycle hardening (rotation 2)

**When:** 2026-06-24 (UTC)  
**Theme:** Report string contract, attention rulings parity, API lifecycle paths, ActiveExperiments UI  
**Why:** Pass 4 covered rules/trends/reports unit tests but lacked a single Python/TypeScript
contract for daily-report navigation strings, API ruling parity between `/experiment/active`
and `/experiment/trend-summary`, and parent-level `ActiveExperiments` integration tests.

## What changed

| Area | Change |
|---|---|
| `marketmind/experiment_lifecycle_contract.py` | Canonical report phrases + attention rulings |
| `marketmind/reports.py` | Uses contract constants (no string drift) |
| `marketmind/experiment_trend_summary.py` | Shares `ATTENTION_RULINGS` from contract |
| `desktop/src/experimentAttention.ts` | Exports `ATTENTION_RULINGS` for cross-check |
| `tests/test_experiment_lifecycle_hardening.py` | 8 tests: contract cross-check, report emission, API parity |
| `desktop/src/components/ActiveExperiments.test.tsx` | 7 integration tests: filters, focus, chart, end experiment |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0
python scripts/local_ci.py                                # exit 0
```

## What could still break

- Product-specific risk strings remain dynamic (product name + CAC amounts) — only suffix/prefix contract tested.
- `ActiveExperiments` checklist/mistakes sections not exercised at integration level (child API mocks only).

## Verification checklist

- [x] Daily report navigation constants match Python contract
- [x] Attention rulings match `experimentAttention.ts`
- [x] Active + trend-summary rulings agree for same snapshot
- [x] `attention_only=true` filters trend API
- [x] Ended experiments drop out of trend summary but remain in active list
- [x] ActiveExperiments filters, focus, chart, and status patch wired through parent
