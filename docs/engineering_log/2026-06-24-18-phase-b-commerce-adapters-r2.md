# Phase B pass 12 — Commerce adapters hardening (rotation 2)

**When:** 2026-06-24 (UTC)  
**Theme:** Secret mask contract, action aliases, env canonical names, API/CLI paths  
**Why:** Pass 5 covered simulate paths and basic readiness snapshots but lacked a single
contract for mask vectors and commerce action aliases, SHOPIFY_ADMIN_ACCESS_TOKEN
readiness, live-writes readiness API warnings, execute/log HTTP leakage checks, and
`check_commerce_config.py` subprocess safety.

## What changed

| Area | Change |
|---|---|
| `marketmind/commerce_adapters_contract.py` | Secret mask vectors + commerce action aliases + env name re-exports |
| `marketmind/commerce_integrations.py` | Uses canonical env names from contract |
| `marketmind/commerce_approval_policy.py` | Imports aliases from contract |
| `tests/test_commerce_adapters_hardening.py` | +10 tests: mask vectors, aliases, admin token, readiness/health, execute/log API, CLI |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (567 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- Gmail refresh tokens are not in the log mask regex — tests rely on adapters not logging them.
- Live OAuth refresh over HTTPS still sends secrets; only simulate/readiness paths covered.

## Verification checklist

- [x] `SECRET_MASK_VECTORS` redacted by `mask_secret`
- [x] Commerce action aliases match `normalize_commerce_action`
- [x] `SHOPIFY_ADMIN_ACCESS_TOKEN` counts as configured
- [x] `/operator/readiness` commerce snapshot + health warnings with live_writes
- [x] `/execute` and `/execute/log` never echo Stripe key
- [x] `check_commerce_config.py` stdout has no secrets
