# Phase B pass 20 — Deploy/CI hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Deploy/CI contract step names, env vars, verify failure formatter  
**Why:** Pass 13 (`2026-06-24-19`) added integrations leak checks and workflow parity but
lacked a dedicated contract test module (pattern from passes 15–19), explicit
local-ci step/env constants, per-marker leak failure matrix, and
`deploy_verify.py` wired to contract failure/success strings.

## What changed

| Area | Change |
|---|---|
| `deploy_ci_contract.py` | Step names, env vars, Python version, failure/success lines, leak formatter |
| `deploy_verify.py` | Uses contract constants + `format_integrations_leak_failure` |
| `tests/test_deploy_ci_contract.py` | 21 tests: workflow parity, leak matrix, endpoint smoke, DEPLOYMENT.md |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 708; stale inventory includes 687 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (708 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- Frontend `npm test` / `npm run build` not mirrored in `local_ci.py` (hosted job only).
- Integrations leak check is substring-based; novel secret formats need contract updates.

## Verification checklist

- [x] `LOCAL_CI_BACKEND_STEP_NAMES` matches `CI_STEPS`
- [x] `FULL_CI_EXTRA_STEP_NAMES` matches `FULL_CI_EXTRA`
- [x] Verify/readiness scripts document contract env vars and `--api` flag
- [x] `ci.yml` Python version and deploy-verify job name match contract
- [x] Each `INTEGRATIONS_SECRET_LEAK_MARKERS` entry fails deploy verify
- [x] Commerce contract re-exports deploy leak markers unchanged
- [x] All contract endpoints return 200 on in-process TestClient
- [x] `DEPLOYMENT.md` lists all verify endpoints
