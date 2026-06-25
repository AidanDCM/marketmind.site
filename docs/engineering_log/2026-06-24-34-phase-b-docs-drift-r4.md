# Phase B pass 28 — Docs drift hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** Rotation 4 contract doc parity, vitest inventory guards, engineering-log SSOT  
**Why:** Pass 21 (`2026-06-24-27`) added rotation 3 contract table and
`test_docs_drift_contract.py` but passes 22–27 deepened six contracts without a
rotation 4 SSOT table, vitest minimum guards in inventory docs, or engineering-log
file parity checks per r4 theme.

## What changed

| Area | Change |
|---|---|
| `docs_contract.py` | `PHASE_B_ROTATION_4_CONTRACTS`, pass 22–28 constants, stale inventory |
| `tests/test_docs_drift_contract.py` | +23 tests: rotation 4 parity, pass 28 status, vitest guards |
| `MARKETMIND_TESTING_AND_EVIDENCE.md` | Passes 22–28 contract table |
| `OPERATING_INDEX.md` | Pass 28 complete; rotation 4 complete |
| `SLICE_WORKFLOW.md` | 860+ pytest / 29+ Vitest inventory |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (860 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- `MIN_PYTEST_CASES` / `MIN_VITEST_FILES` must bump when suites grow.
- Stale substring guard can false-positive on port `8000` if `800` is listed as stale.
- Engineering-log glob uses theme slug; renames need contract updates.

## Verification checklist

- [x] All six rotation 4 contract modules + tests exist on disk
- [x] Testing manual documents passes 22–28 and each contract module/test
- [x] `OPERATING_INDEX` cites pass 28 and docs drift r4
- [x] `CHANGELOG` documents rotation 4 bookend passes (22 and 27)
- [x] Each rotation 4 theme has an `*-r4.md` engineering log
- [x] Inventory docs cite current pytest (860) and Vitest (29) minimums
- [x] Current pytest minimum not listed in `STALE_PYTEST_INVENTORY`
