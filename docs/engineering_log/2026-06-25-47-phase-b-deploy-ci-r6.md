# Phase B pass 41 — Deploy/CI hardening (rotation 6)

**When:** 2026-06-25 (UTC)  
**Theme:** Health-wait loop SSOT, DeployVerifyResult field parity, stderr routing, rk_live_ marker  
**Why:** Pass 34 (`2026-06-24-40`) guarded readiness/integrations fetch failures and workflow
job parity but did not assert CI health-wait sleep/curl fragments, `DeployVerifyResult`
metadata on success, verify-script stderr routing for `FAIL` lines,
`check_operator_readiness.py --api` default base URL parity, `/health` version SSOT,
or `rk_live_` in integrations leak markers / `mask_secret`.

## What changed

| Area | Change |
|---|---|
| `deploy_ci_contract.py` | Health-wait sleep/curl fragments, result fields, `rk_live_` marker |
| `tests/test_deploy_ci_contract.py` | +8 tests: wait loop, metadata, stderr, version parity |
| `logging_config.py` | `mask_secret` redacts Stripe restricted keys (`rk_live_`) |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 994; pass 41; stale inventory includes 985 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (994 passed)
python scripts/local_ci.py                                # exit 0
```

No new desktop Vitest — deploy/CI is backend/workflow only.

## What could still break

- Frontend `npm test` / `npm run build` remain GitHub Actions only (not `local_ci.py`).
- Health wait loop in `ci.yml` is substring-guarded, not executed in contract tests.
- Substring leak markers may miss novel secret formats beyond the current set.

## Verification checklist

- [x] `ci.yml` health-wait loop documents sleep seconds and curl-break fragment
- [x] `deploy_verify.py` documents all four `CI_DEPLOY_VERIFY_ENDPOINTS`
- [x] `DeployVerifyResult` dataclass fields match contract tuple
- [x] Verify success populates `health_version`, `safe_to_operate`, `ready`
- [x] `check_operator_readiness.py --api` default base matches contract
- [x] Verify script routes `FAIL` lines to stderr and exits 1 on failure
- [x] `/health` version matches `HEALTH_EXPECTED_VERSION`
- [x] `rk_live_` in leak markers and redacted by `mask_secret`
