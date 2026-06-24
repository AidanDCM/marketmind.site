---
name: testing-marketmind-slice
description: Test a single MarketMind feature slice (Overview link, operator panel, API). Use on every proceed during Phase A slice building.
---

# MarketMind Slice Testing

Use when implementing one Overview/operator slice in MarketMind Autopilot.

## Before coding

Read `SLICE_WORKFLOW.md`, `AGENTS.md`, and the latest `CHANGELOG.md` slice entry.

## Implementation rules

- One testable slice per `proceed`
- Smallest diff; match existing component patterns
- Regression test encodes the failure prevented (name or docstring)

## Required verification (record all in engineering log)

```powershell
python -m ruff check .
python -m pytest -q
python -m pytest -q tests/test_<relevant>.py
```

If `desktop/` changed:

```powershell
cd desktop
npm test -- <changed-test-file-or-dir>
npm run build
```

Optional evidence gate:

```powershell
python scripts/local_ci.py
```

## Desktop slice patterns

| Change type | Test location |
|---|---|
| Overview metric link | `OverviewReport*Metrics.test.tsx` |
| Health/readiness panel | `OperatorHealthPanel.test.tsx`, `OperatorReadinessBanner.test.tsx` |
| Report line navigation | `dailyReportNavigation.test.ts` + card tests |
| Message parser | `readinessBannerActions.test.ts`, `preflightSummaryActions.test.ts` |

## Required docs (same PR)

1. `CHANGELOG.md` — slice N entry
2. `OPERATING_INDEX.md` — slice counter
3. `docs/engineering_log/YYYY-MM-DD-<slug>.md` — verbose ledger entry

## PR workflow

Commit → push → `gh pr create` → merge → sync `main` → delete branch (unless Aidan says otherwise).

## Never

- Bypass approval gate in tests (use dry-run/fakes)
- Skip engineering log for "small" UI links
- Claim tests passed without command output in the log entry
