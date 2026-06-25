# Phase B pass 38 — Overview navigation hardening (rotation 6)

**When:** 2026-06-24 (UTC)  
**Theme:** Trend min-days fragment, daily report response keys, attention-only refetch Vitest  
**Why:** Pass 31 (`2026-06-24-37`) guarded trend `as_of`/`days` max edges and health-panel
View snapshots but did not assert `days=0` min fragment, daily report date-scoped response
keys, trend default days when omitted, `attention_only` client path parity, reports router
date query documentation, trend empty-state attention prefix, run-cycle empty-date detail on
Overview contract tests, or attention-only toggle refetch in Vitest.

## What changed

| Area | Change |
|---|---|
| `overview_navigation_contract.py` | Min-days fragment, daily report keys, pending path, empty-state prefix |
| `tests/test_overview_navigation_contract.py` | +8 tests: daily report scope, default days, client/router parity |
| `Overview.test.tsx` | +1 test: attention-only toggle refetches with `attentionOnly=true` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 964; pass 38; stale inventory includes 955 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (964 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `Overview.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- Secondary-metric CAC vs contribution-profit title overlap — parent test uses last match.
- No Playwright e2e for `localStorage` date persistence across reload.
- `days=21` accepted by API but not in desktop lookback dropdown.

## Verification checklist

- [x] `days=0` returns 422 with min-days contract fragment
- [x] Run-cycle empty `date=` returns 422 with contract detail
- [x] Reports router documents daily date query param
- [x] Daily report `date=` scopes response `date` key and contract keys
- [x] Trend summary defaults to contract lookback when `days` omitted
- [x] Desktop client documents `attention_only` and pending approvals path
- [x] Empty DB trend summary has zero needs_attention_count
- [x] Preferences exports `TREND_DAY_OPTIONS` alias
- [x] Trend empty state documents attention prefix and View all experiments
- [x] Overview component documents `fetchPendingApprovals`
- [x] Run-cycle router documents empty-date guard
- [x] Attention-only toggle refetches trend with `attentionOnly=true` in Vitest
