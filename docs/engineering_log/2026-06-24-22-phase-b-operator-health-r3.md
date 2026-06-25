# Phase B pass 16 — Operator health hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Contract formatters for blockers/warnings; Python/TypeScript regex parity  
**Why:** Pass 9 centralized integration warning strings but blocker and snapshot-gap
messages were still inline f-strings. Desktop `readinessBannerActions.ts` regex parsers
could drift from backend output without shared formatters or contract tests.

## What changed

| Area | Change |
|---|---|
| `operator_health_contract.py` | Formatters, regex patterns, API paths, warning prefixes |
| `operator_preflight.py` | Uses `format_pending_approvals_blocker` / `format_experiment_ruling_blocker` |
| `operator_health.py` | Uses `format_missing_snapshot_warning` |
| `tests/test_operator_health_contract.py` | 14 tests: regex parity, API paths, kill ruling, strict readiness |
| `OperatorHealthPanel.test.tsx` | Preflight blocker list links experiment ruling to View experiment |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 644 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (644 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `OperatorHealthPanel.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Dynamic snapshot-gap ID lists beyond truncation still only prefix-tested via regex group 3.
- `check_operator_readiness.py` subprocess against a live pending approval uses the
  operator's real DB path — not exercised in contract tests (only `--help` checked).

## Verification checklist

- [x] Contract formatters match desktop `readinessBannerActions` regex patterns
- [x] Kill-ruling experiment surfaces contract-formatted preflight blocker
- [x] `/operator/preflight`, `/readiness`, `/health-panel` return 200 on empty DB
- [x] Strict readiness fails when operator-log warning present
- [x] Health panel preflight blocker list links experiment ruling in UI
