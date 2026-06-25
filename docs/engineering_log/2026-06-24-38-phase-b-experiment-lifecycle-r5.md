# Phase B pass 32 — Experiment lifecycle hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Status/note 404 edges, portfolio response keys, active-list shape, notes UI wiring  
**Why:** Pass 25 (`2026-06-24-31`) added per-experiment detail suffixes, preference keys, and
reactivate Vitest but did not guard status-patch invalid fragment, note/mistakes 404 with
contract detail, portfolio/active entry response keys, status ended_at round-trip, notes GET
empty-list behavior for unknown experiments, evaluate missing-body 422, or desktop Add-note
button wiring.

## What changed

| Area | Change |
|---|---|
| `experiment_lifecycle_contract.py` | Router path, validation fragments, portfolio/active keys, notes UI labels |
| `tests/test_experiment_lifecycle_contract.py` | +9 tests: 404/422 edges, response keys, status round-trip, notes behavior |
| `ActiveExperiments.test.tsx` | +1 test: Add note calls `addExperimentNote` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 903; stale inventory includes 894 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (903 passed)
python scripts/local_ci.py                                # exit 0
```

Desktop Vitest: `ActiveExperiments.test.tsx` (+1 test); rely on CI frontend job if
`npm` unavailable.

## What could still break

- New per-experiment endpoints must be added to `LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES`.
- Checklist only renders for `active` status — ended experiments hide scale gate UI.
- GET notes returns `[]` for unknown experiments (by design); POST notes returns 404.

## Verification checklist

- [x] Experiments router documents status/note validation fragments
- [x] Invalid status patch returns 422 with contract fragment
- [x] Empty note body returns 422 with contract detail
- [x] Unknown experiment POST note and GET mistakes return 404
- [x] Unknown experiment GET notes returns empty list (documented in router)
- [x] Portfolio response includes contract keys
- [x] Active list entries include contract keys
- [x] Patch active→ended sets `ended_at`
- [x] Desktop client documents patch/note/checklist/mistakes functions
- [x] ActiveExperiments documents notes placeholder, Add button, empty label
- [x] Evaluate endpoint rejects empty body with 422
- [x] Add note button calls `addExperimentNote` in Vitest
