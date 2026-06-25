# 2026-06-24 — No-report empty Score Product link (slice 119)

- **Author:** AI agent (Cursor)
- **Commit(s)/PR:** (this PR)
- **Where:** `desktop/src/components/OverviewReportEmptyState.tsx`, `desktop/src/components/Overview.tsx`, tests
- **When:** 2026-06-24 UTC
- **What changed:**
  - Extracted `OverviewReportEmptyState` from Overview inline empty block.
  - Preserved **Record a snapshot for {date}** action (slice 87).
  - Added **Score a product** when `onOpenScoreProduct` is wired — aligns with slice 105 no-experiments recommendation path.
- **Why (evidence):** Empty report state previously only routed to Snapshots; operators with no snapshot data for a date may need to start the experiment pipeline via Score Product instead.
- **What could still break:** Empty report does not strictly mean zero active experiments (could be missing snapshots only); Score Product is still a reasonable next step but not always correct.
- **Verification:**
  - `python -m pytest -q` → 466 passed
  - `python -m ruff check .` → all checks passed
  - `python scripts/local_ci.py` → PASS
  - `OverviewReportEmptyState.test.tsx` — snapshot, score product, negative handler case
- **Follow-up:** Phase B — audit all Overview empty states have Vitest coverage in CI frontend job.
