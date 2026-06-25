# Phase B pass 31 — Overview navigation hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Trend as_of ISO validation, days max 422, daily-report date query, health-panel snapshot navigation  
**Why:** Pass 24 (`2026-06-24-30`) added trend query params, lookback matrix, and health-panel
Show attention wiring but did not guard invalid `as_of` ISO dates, `days=91` max edge with
contract fragment, daily-report `date` query in client, preference read helpers,
`trend-summary` response keys, `overviewDailyCycle` attention-only passthrough, or health-panel
View snapshots through the Overview parent.

## What changed

| Area | Change |
|---|---|
| `overview_navigation_contract.py` | Router paths, trend validation details, response keys, UI labels |
| `tests/test_overview_navigation_contract.py` | +10 tests: 422 edges, client parity, preference helpers, response keys |
| `Overview.test.tsx` | +1 test: View snapshots from health panel through Overview |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 894; stale inventory includes 884 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (894 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `Overview.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Secondary-metric CAC vs contribution-profit title overlap — parent test uses last match.
- No Playwright e2e for `localStorage` date persistence across reload.
- `days=21` is accepted by API (within 1–90) but not in desktop lookback dropdown.

## Verification checklist

- [x] Experiments router documents trend query params and as_of validation details
- [x] Invalid `as_of` ISO and empty `as_of=` return 422 with contract detail
- [x] `days=91` returns 422 with max-days fragment
- [x] Daily report date query documented in desktop client
- [x] `lookbackOptions.ts` exports `isLookbackDayOption`
- [x] `overviewPreferences.ts` exports read preference helpers
- [x] Overview documents `runOverviewDailyCycle` / `handleRunCycle`
- [x] Trend summary response includes contract keys
- [x] `overviewDailyCycle.ts` passes `attentionOnly` through fetch bundle
- [x] Trend empty state documents View all experiments button
- [x] Health panel View snapshots opens recorder through Overview parent
