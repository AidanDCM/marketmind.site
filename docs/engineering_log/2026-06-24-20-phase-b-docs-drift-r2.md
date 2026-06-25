# Phase B pass 14 — Docs drift hardening (rotation 2)

**When:** 2026-06-24 (UTC)  
**Theme:** Operator docs vs deploy verify endpoints, suite inventory, Phase B rotation 2  
**Why:** Pass 13 added `/operator/integrations` secret-leak checks to
`verify_marketmind_deploy.py`, but `DEPLOYMENT.md` and the testing manual still
documented only three verify endpoints. Active operator docs could also regress to
stale inventory counts (512, 556, 567) without a guard beyond pass 7's `465` check.

## What changed

| Area | Change |
|---|---|
| `marketmind/docs_contract.py` | `STALE_PYTEST_INVENTORY`, `STALE_VITEST_INVENTORY`, `DEPLOYMENT_DOC_PATH`; `MIN_PYTEST_CASES` → 585 |
| `tests/test_docs_drift_hardening.py` | 7 regression tests for deploy-verify doc parity and stale inventory |
| `docs/DEPLOYMENT.md` | `/operator/integrations` curl + forbidden secret substrings |
| `MARKETMIND_TESTING_AND_EVIDENCE.md` | Deploy CI contract endpoints, rotation 2 table, hardening test file |
| `OWNER_MANUAL.md` | Verify-deploy row mentions integrations secret check |
| `OPERATING_INDEX.md` | Pass 14 complete, ~585 pytest inventory |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (585 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- `MIN_PYTEST_CASES` must be bumped when the suite grows or `test_docs_drift.py` fails.
- Engineering-log archive entries still cite 512/567 pytest (intentional history).
- Vitest guard is file-count based, not per-test-case.

## Verification checklist

- [x] DEPLOYMENT documents all four `CI_DEPLOY_VERIFY_ENDPOINTS`
- [x] Testing manual cites `deploy_ci_contract` and `test_docs_drift_hardening.py`
- [x] Active operator docs have no stale 512/556/567 pytest inventory
- [x] `tests/test_docs_drift_hardening.py` passes
