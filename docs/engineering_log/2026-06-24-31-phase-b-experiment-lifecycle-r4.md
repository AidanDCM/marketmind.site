# Phase B pass 25 — Experiment lifecycle hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** Per-experiment API path contract, ActiveExperiments UI parity, status/note 422 edges  
**Why:** Pass 18 (`2026-06-24-24`) added lifecycle API smoke, report suffix matrix, and
ActiveExperiments checklist/mistakes Vitest but did not guard per-experiment detail
suffixes (`status`, `notes`, `checklist`, `mistakes`) in client + router, preference
localStorage keys, UI label parity, empty-note 422, or reactivate-from-ended desktop flow.

## What changed

| Area | Change |
|---|---|
| `experiment_lifecycle_contract.py` | Detail suffixes, status filters, UI labels, preference keys |
| `tests/test_experiment_lifecycle_contract.py` | +16 tests: client/router parity, 404/422 edges, note round-trip |
| `ActiveExperiments.test.tsx` | +1 test: reactivate ended experiment |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 800; stale inventory includes 784 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (800 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ActiveExperiments.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- New per-experiment endpoints must be added to `LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES`.
- Checklist only renders for `active` status — ended experiments hide scale gate UI.
- Trend query 422 edges remain guarded by `test_overview_navigation_contract.py`.

## Verification checklist

- [x] Desktop client documents lifecycle list + detail API paths
- [x] Experiments router documents all detail suffixes
- [x] Invalid status patch returns 422; unknown experiment returns 404
- [x] Empty note body returns 422
- [x] Checklist/mistakes/notes GET smoke on seeded experiment
- [x] ActiveExperiments component documents attention filter and section headers
- [x] `activeExperimentsPreferences.ts` exports filter helpers and storage keys
- [x] `experimentAttention.ts` rulings match contract `ATTENTION_RULINGS`
- [x] Reactivate button calls `patchExperimentStatus` with `active`
