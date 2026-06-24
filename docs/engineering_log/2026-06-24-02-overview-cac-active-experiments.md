# 2026-06-24 — Overview CAC metric → Active Experiments (slice 115)

- **Author:** AI agent (Cursor)
- **Commit(s)/PR:** (this PR)
- **Where:** `desktop/src/components/OverviewReportPrimaryMetrics.tsx`, `desktop/src/components/Overview.tsx`, tests
- **When:** 2026-06-24 UTC
- **What changed:** Daily report **CAC** metric card is clickable and opens **Active Experiments** when `onOpenActiveList` is wired from Overview. Added negative test: no title/handler when callback omitted.
- **Why (evidence):** Continue Overview primary-metrics navigation chain (Orders/Revenue → Live Data, Ad Spend → Import History, Contribution Profit → Active Experiments). CAC is experiment-performance context; operator should jump to active list to compare CAC vs BEP per experiment.
- **What could still break:** If multiple components use identical `title="Open Active Experiments"`, tests must scope by card; secondary metrics Contribution Profit also uses same title (different component file).
- **Verification:**
  - `python -m pytest -q` → 466 passed
  - `python -m ruff check .` → all checks passed
  - `python -m pytest -q tests/test_local_ci.py` → pass
  - Desktop: `npm test -- src/components/OverviewReportPrimaryMetrics.test.tsx` — not run in agent shell (npm not on PATH); CI frontend job covers this.
- **Follow-up:** Link Refund Rate / Add-to-Cart in secondary metrics when elevated (slice 116+).
