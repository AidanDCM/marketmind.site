# Phase B pass 39 — Experiment lifecycle hardening (rotation 6)

**When:** 2026-06-24 (UTC)  
**Theme:** Reactivate clears ended_at, response key SSOT, checklist/mistakes 404 detail, notes Vitest  
**Why:** Pass 32 (`2026-06-24-38`) guarded status/note 404 edges and Add-note Vitest but did not
assert ended→active reactivate clears `ended_at`, status/evaluate/checklist/mistakes/note
response key SSOT, portfolio counts with seeded experiments, checklist 404 detail fragment,
router reactivate docstring parity, `evaluateExperiment` client wiring, or focused-card
`getExperimentNotes` load in Vitest.

## What changed

| Area | Change |
|---|---|
| `experiment_lifecycle_contract.py` | Status constants, body keys, evaluate/checklist/mistakes/note response keys |
| `tests/test_experiment_lifecycle_contract.py` | +9 tests: reactivate round-trip, response keys, portfolio count |
| `ActiveExperiments.test.tsx` | +1 test: focused card loads notes via `getExperimentNotes` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 973; pass 39; stale inventory includes 964 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (973 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ActiveExperiments.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- New per-experiment endpoints must be added to `LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES`.
- Checklist only renders for `active` status — ended experiments hide scale gate UI.
- GET notes returns `[]` for unknown experiments (by design); POST notes returns 404.

## Verification checklist

- [x] Patch ended→active clears `ended_at` via API
- [x] Status patch response includes contract keys
- [x] Evaluate response includes contract keys
- [x] Checklist response includes contract keys (and item keys when present)
- [x] Mistakes response includes contract keys on empty seeded experiment
- [x] Note POST response includes contract keys
- [x] Portfolio reflects seeded active experiment counts
- [x] Router documents reactivate clears `ended_at` and body field keys
- [x] Desktop client documents `evaluateExperiment`
- [x] Checklist unknown experiment 404 includes not-found detail
- [x] Focused experiment card loads notes via `getExperimentNotes` in Vitest
