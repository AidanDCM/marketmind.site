# 2026-06-24 — Conversion zero-order link (slice 117)

- **Author:** AI agent (Cursor)
- **Commit(s)/PR:** (this PR)
- **Where:** `desktop/src/overviewReportSecondaryMetrics.ts`, `desktop/src/components/OverviewReportSecondaryMetrics.tsx`, tests
- **When:** 2026-06-24 UTC
- **What changed:**
  - Added `shouldLinkConversionToExperiments`: true when `ad_spend > 0 && orders === 0`.
  - Conversion metric card opens Active Experiments with title `Open Active Experiments — review conversion`.
  - Unit tests for threshold; component tests for link present/absent.
- **Why (evidence):** Completes secondary metrics navigation. Zero-order spend is a daily report risk (`ZERO_ORDER_SPEND_RISK` → Active Experiments in slice 106); conversion card is the natural funnel metric when spend produces no orders.
- **What could still break:** Conversion and Add-to-Cart may both link in the same zero-order/low-ATC scenario — intentional (different operator mental models).
- **Verification:**
  - `python -m pytest -q` → 466 passed
  - `python -m ruff check .` → all checks passed
  - `python scripts/local_ci.py` → PASS
- **Follow-up:** Overview primary/secondary metric grid fully linked; next slices may shift to other surfaces (trend header, empty states) or Phase B hardening.
