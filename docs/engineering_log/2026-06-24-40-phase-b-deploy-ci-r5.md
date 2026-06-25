# Phase B pass 34 — Deploy/CI hardening (rotation 5)

**When:** 2026-06-24 (UTC)  
**Theme:** Readiness/integrations fetch failure prefixes, health response keys, workflow job parity  
**Why:** Pass 27 (`2026-06-24-33`) added CI boot constants and health/preflight failure matrix but did not
guard readiness/integrations fetch error prefixes, `/health` response key contract, verify script
exit codes, deploy-verify job script + `MARKETMIND_API_BASE` wiring, workflow job display names,
or uvicorn app target string parity.

## What changed

| Area | Change |
|---|---|
| `deploy_ci_contract.py` | Health response keys, uvicorn target, job names, verify module path |
| `tests/test_deploy_ci_contract.py` | +7 tests: fetch error edges, health keys, workflow/script parity |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 917; stale inventory includes 910 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (917 passed)
python scripts/local_ci.py                                # exit 0
```

No new desktop Vitest — deploy/CI is backend/workflow only.

## What could still break

- Frontend `npm test` / `npm run build` remain GitHub Actions only (not `local_ci.py`).
- Health wait loop in `ci.yml` is substring-guarded, not executed in contract tests.
- Substring leak markers may miss novel secret formats.

## Verification checklist

- [x] Deploy verify module documents readiness/integrations fetch failure prefixes
- [x] `/health` returns contract `status` and `version` keys
- [x] Readiness fetch error fails with `operator/readiness:` prefix
- [x] Integrations fetch error fails with `operator/integrations:` prefix
- [x] `local_ci.py` documents TEST_LOG path and `format_test_log_entry`
- [x] Verify script documents `verify_marketmind_deploy` and exit codes
- [x] `ci.yml` runs both deploy-verify scripts with `MARKETMIND_API_BASE`
- [x] Workflow documents backend/frontend job names and uvicorn app target
