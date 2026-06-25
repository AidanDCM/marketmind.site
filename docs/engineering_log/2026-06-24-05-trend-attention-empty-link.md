# 2026-06-24 — Trend attention empty link (slice 118)

- **Author:** AI agent (Cursor)
- **Commit(s)/PR:** (this PR)
- **Where:** `desktop/src/components/OverviewTrendEmptyState.tsx`, `desktop/src/components/Overview.tsx`, tests
- **When:** 2026-06-24 UTC
- **What changed:**
  - Extracted `OverviewTrendEmptyState` for the CAC trends card empty message.
  - When **Attention only** is checked and no experiments match, shows **View all experiments** → Active Experiments list.
  - Link hidden when not in attention-only mode or when handler omitted.
- **Why (evidence):** Operators enabling attention-only filter and seeing an empty table had no exit ramp except manually unchecking the box and navigating sidebar. Mirrors other Overview empty-state shortcuts (slice 87 snapshots empty state).
- **What could still break:** Link opens full active list but does not auto-clear the attention-only checkbox on Overview (operator may return and still see empty until they uncheck).
- **Verification:**
  - `python -m pytest -q` → 466 passed
  - `python -m ruff check .` → all checks passed
  - `python scripts/local_ci.py` → PASS
  - `OverviewTrendEmptyState.test.tsx` — happy path + two negative cases
- **Follow-up:** Optionally clear attention-only preference when navigating from empty state; or add Score Product link on no-report empty state.
