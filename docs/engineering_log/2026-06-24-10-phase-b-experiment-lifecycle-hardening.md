# 2026-06-24 — Phase B: Experiment lifecycle hardening (pass 4)

## Why

Phase B rotation item 4: **experiment lifecycle** — rules, snapshots, trends, daily report
math. Core paths had unit tests but gaps remained linking backend output strings to
desktop navigation parsers and API end-to-end flows.

## Where

- `tests/test_reports.py` — low ATC risk, ROAS lessons, add-to-cart aggregation
- `tests/test_experiment_trend_summary.py` — CAC down/flat, no-snapshot rows, scale attention
- `tests/test_experiment_rules.py` — kill priority over pause when both signals fire
- `tests/test_api.py` — daily report + trend-summary API integration
- `desktop/src/dailyReportNavigation.test.ts` — backend ATC risk + healthy ROAS lesson strings

## When

2026-06-24 UTC (Phase B pass 4).

## Verification

```text
python -m ruff check .                    -> exit 0
python -m pytest -q                       -> 492 passed
python scripts/local_ci.py                -> PASS
cd desktop && npm test                    -> CI frontend job
```

## Gaps remaining

- Snapshot trend endpoint vs experiment trend-summary overlap not deduplicated (by design).
- Phase B rotation next: commerce adapters or deploy/CI.
