# Phase B pass 19 — Commerce adapters hardening (rotation 3)

**When:** 2026-06-24 (UTC)  
**Theme:** Commerce API path contract, deploy leak-marker parity, handler/policy matrix  
**Why:** Pass 12 (`2026-06-24-18`) added mask vectors and execute/log Stripe checks but
lacked a dedicated contract test module (pattern from passes 15–18), deploy
`INTEGRATIONS_SECRET_LEAK_MARKERS` cross-check, Shopify execute API coverage,
Gmail integration key whitelist, and desktop client path parity for
sources/imports.

## What changed

| Area | Change |
|---|---|
| `commerce_adapters_contract.py` | API paths, handler actions, deploy leak markers, Gmail keys, CLI path |
| `tests/test_commerce_adapters_contract.py` | 20 tests: mask/deploy parity, handlers, integrations, Shopify execute, sources 409 |
| `docs_contract.py` | `MIN_PYTEST_CASES` → 687; stale inventory includes 667 |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (687 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- Gmail refresh tokens are not in `logging_config._SECRET_PATTERN` — adapters must
  never log them; contract tests only whitelist integration JSON keys.
- Live OAuth refresh over HTTPS still sends secrets; only simulate/readiness/API
  paths covered.

## Verification checklist

- [x] Deploy leak markers redacted by `mask_secret`
- [x] Commerce handler actions match executor registry and HIGH_RISK policy
- [x] Desktop `client.ts` documents commerce read/execute/source/import paths
- [x] `/operator/integrations` + `/operator/readiness` secret-free with creds in env
- [x] Gmail integration payload exposes contract keys only
- [x] `/sources/stripe/orders` safe-fails 409 without credentials
- [x] Shopify `/execute` + `/execute/log` dry-run secret-free
- [x] `check_commerce_config.py` stdout has no deploy leak markers
