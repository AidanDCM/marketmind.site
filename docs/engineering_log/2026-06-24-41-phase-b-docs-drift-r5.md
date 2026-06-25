# Phase B pass 35 — Docs drift hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Rotation 5 contract SSOT, vitest inventory guards, engineering-log parity  
**Why:** Pass 28 (`2026-06-24-34`) added rotation 4 contract table and
`test_docs_drift_contract.py` depth but passes 29–34 deepened six contracts without a
rotation 5 SSOT table, operating-index rotation-complete status, or engineering-log
file parity checks per r5 theme.

## What changed

| Area | Change |
|---|---|
| `docs_contract.py` | `PHASE_B_ROTATION_5_CONTRACTS`, pass 29–35 constants; stale inventory includes 917 |
| `tests/test_docs_drift_contract.py` | +18 tests: rotation 5 parity, pass 35 status, operating index |
| `MARKETMIND_TESTING_AND_EVIDENCE.md` | Passes 29–35 contract table |
| `OPERATING_INDEX.md` | Pass 35 complete; rotation 5 complete |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (935 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- `MIN_PYTEST_CASES` / `MIN_VITEST_FILES` must bump when suites grow.
- Stale substring guard can false-positive on port `8000` if `800` is listed as stale.
- Engineering-log glob uses theme slug; renames need contract updates.

## Verification checklist

- [x] All six rotation 5 contract modules + tests exist on disk
- [x] Testing manual documents passes 29–35 and each contract module/test
- [x] `OPERATING_INDEX` cites pass 35, docs drift r5, and rotation 5 complete
- [x] `CHANGELOG` documents rotation 5 bookend passes (29 and 34)
- [x] Each rotation 5 theme has an `*-r5.md` engineering log
- [x] Inventory docs cite current pytest (935) and Vitest (29) minimums
- [x] Current pytest minimum not listed in `STALE_PYTEST_INVENTORY`
