# Phase B pass 21 — Docs drift hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Rotation 3 contract doc parity, dedicated docs drift contract tests  
**Why:** Pass 14 (`2026-06-24-20`) added deploy-verify doc guards and stale inventory lists
but rotation 3 (passes 15–20) added six new `*_contract.py` modules without a single
SSOT table in `docs_contract.py` or `test_docs_drift_contract.py` guarding that
operator docs stay aligned.

## What changed

| Area | Change |
|---|---|
| `docs_contract.py` | `PHASE_B_ROTATION_3_CONTRACTS`, drift test files, inventory doc paths |
| `tests/test_docs_drift_contract.py` | 20 tests: rotation 3 file parity, testing manual table, operator guards |
| `MARKETMIND_TESTING_AND_EVIDENCE.md` | Passes 15–21 contract table + drift guard file list |
| `AGENTS.md` / `SLICE_WORKFLOW.md` | Reference `docs_contract` and `test_docs_drift*.py` |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 728; stale inventory includes 708 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (728 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- `MIN_PYTEST_CASES` must be bumped when the suite grows.
- Engineering-log archive entries still cite historical pytest counts (intentional).
- Vitest guard remains file-count based, not per-test-case.

## Verification checklist

- [x] All six rotation 3 contract modules + tests exist on disk
- [x] Testing manual documents passes 15–21 and each contract module/test
- [x] `DOCS_DRIFT_TEST_FILES` all exist and cited in testing manual
- [x] `AGENTS.md` and `SLICE_WORKFLOW.md` reference docs drift guards
- [x] `OPERATING_INDEX` cites `test_docs_drift_contract.py`
- [x] Inventory docs cite current pytest minimum (728)
