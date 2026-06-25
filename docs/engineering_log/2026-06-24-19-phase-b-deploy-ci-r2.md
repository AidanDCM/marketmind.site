# Phase B pass 13 — Deploy/CI hardening (rotation 2)

**When:** 2026-06-24 (UTC)  
**Theme:** Deploy verify integrations check, CI workflow contract, endpoint parity  
**Why:** Pass 6 aligned `local_ci --full` with deploy-verify scripts but deploy verification
did not fetch `/operator/integrations` or guard against credential leakage in API smoke
tests — a gap called out in the pass 6 engineering log.

## What changed

| Area | Change |
|---|---|
| `marketmind/deploy_ci_contract.py` | Workflow paths, verify endpoints, secret leak markers, frontend steps |
| `marketmind/deploy_verify.py` | GET `/operator/integrations` + forbidden substring check |
| `marketmind/local_ci.py` | Imports deploy scripts from contract |
| `tests/test_deploy_ci_hardening.py` | CI workflow parity + endpoint contract tests |
| `tests/test_deploy_verify.py` | Integrations leak/unreachable/env-credentials tests |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (578 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- Frontend `npm test` / `npm run build` not mirrored in `local_ci.py` (hosted job only).
- Integrations leak check is substring-based; novel secret formats need contract updates.

## Verification checklist

- [x] `CI_DEPLOY_VERIFY_SCRIPTS` single source in `deploy_ci_contract.py`
- [x] `ci.yml` contains backend, deploy-verify, and frontend job commands
- [x] Deploy verify hits all contract endpoints including integrations
- [x] Leaked `sk_test_` in integrations JSON fails verification
- [x] Live TestClient with env credentials passes without echoing secrets
