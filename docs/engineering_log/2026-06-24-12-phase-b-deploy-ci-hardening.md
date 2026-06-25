# Phase B pass 6 — Deploy/CI hardening

**When:** 2026-06-24 (UTC)  
**Theme:** Align `local_ci.py` with GitHub Actions; strengthen deploy-verify regression tests  
**Why:** CI runs deploy verify **and** operator readiness against a live API, but `local_ci --full`
only ran the first script. Drift between local and hosted gates hides deploy regressions.

## What changed

| Area | Change |
|---|---|
| `marketmind/local_ci.py` | `CI_DEPLOY_VERIFY_SCRIPTS` contract; `FULL_CI_EXTRA` adds `operator_readiness_api` |
| `scripts/local_ci.py` | Docstring updated for `--full` parity |
| `tests/test_local_ci.py` | Workflow file parity, script existence, log formatter, aggregate helpers |
| `tests/test_deploy_verify.py` | TestClient e2e, unreachable endpoints, warnings-only pass |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (512 passed)
python scripts/local_ci.py                                # exit 0
```

`local_ci --full` requires a running API at `MARKETMIND_API_BASE` (same as CI job).

## What could still break

- Frontend CI (`npm test` / `npm run build`) is not mirrored in `local_ci.py` — agents still
  rely on hosted `frontend` job or manual `cd desktop && npm test`.
- Deploy verify does not yet check `/operator/integrations` or commerce credential absence
  (covered in pass 5 unit tests).

## Verification checklist

- [x] `FULL_CI_EXTRA` step names match ci.yml deploy-verify commands
- [x] Deploy verify passes against in-process TestClient (no uvicorn)
- [x] Health/panel fetch failures return structured `DeployVerifyResult` failures
- [x] Warnings alone do not fail deploy verification
