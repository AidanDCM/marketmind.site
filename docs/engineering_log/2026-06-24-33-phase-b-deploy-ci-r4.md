# Phase B pass 27 — Deploy/CI hardening (rotation 4)

**When:** 2026-06-24 (UTC)  
**Theme:** CI workflow boot constants, deploy-verify failure matrix, local_ci helpers  
**Why:** Pass 20 (`2026-06-24-26`) added step/env contract and leak-marker matrix but did not
guard `ci.yml` database URL / uvicorn boot / Node version, deploy-verify health and
preflight failure prefixes, non-fatal health-panel warnings, API token forwarding, or
`format_test_log_entry` / `STATUS_CONTEXT` parity with the contract module.

## What changed

| Area | Change |
|---|---|
| `deploy_ci_contract.py` | CI node/DB/uvicorn constants, deploy failure prefixes, local_ci paths |
| `tests/test_deploy_ci_contract.py` | +18 tests: workflow parity, verify failure edges, token forwarding |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 837; stale inventory includes 819 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (837 passed)
python scripts/local_ci.py                                # exit 0
```

No new desktop Vitest — deploy/CI is backend/workflow only.

## What could still break

- Frontend `npm test` / `npm run build` remain GitHub Actions only (not `local_ci.py`).
- Health wait loop in `ci.yml` is substring-guarded, not executed in contract tests.
- Substring leak markers may miss novel secret formats.

## Verification checklist

- [x] `ci.yml` documents contract DB URL, uvicorn host/port, health wait loop
- [x] Node version and backend ruff/pytest commands match contract
- [x] All `CI_BACKEND_JOBS` and frontend step commands appear in workflow
- [x] `STATUS_CONTEXT` matches `LOCAL_CI_STATUS_CONTEXT`
- [x] `local_ci.py` documents `--full` and TEST_LOG append path
- [x] `format_test_log_entry` records failed step names
- [x] Verify fails on bad health status, fetch errors, preflight blockers
- [x] Readiness blockers listed when `ready` is false
- [x] Health-panel warnings do not fail deploy verify
- [x] Deploy verify forwards `MARKETMIND_API_TOKEN` to fetch callable
