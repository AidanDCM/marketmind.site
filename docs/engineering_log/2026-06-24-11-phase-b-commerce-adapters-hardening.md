# Phase B pass 5 — Commerce adapters hardening

**When:** 2026-06-24 (UTC)  
**Theme:** Stripe / Shopify / Gmail fakes; no secrets in logs or operator-facing responses  
**Why:** Commerce integrations hold live API keys. Operator readiness and execution paths must
never echo credential values — only booleans and simulated IDs.

## What changed

| Area | Change |
|---|---|
| `tests/test_commerce_adapters_hardening.py` | New regression suite: readiness snapshots, simulate responses, client DEBUG logs, Gmail pending gate |
| `tests/test_executor.py` | Live Shopify mock + Gmail simulate: tokens absent from `ExecutionResult.to_dict()` |
| `tests/test_operator.py` | `GET /operator/integrations` with secrets in env returns configured flags only |

## Evidence

```powershell
python -m ruff check .                                    # exit 0
python -m pytest -q                                       # exit 0 (503 passed)
python -m pytest -q tests/test_commerce_adapters_hardening.py  # exit 0 (10 passed)
python scripts/local_ci.py                                # exit 0
```

## What could still break

- Structured logging masker (`logging_config.mask_secret`) covers known patterns only;
  a new credential format would need a pattern + test.
- Live Gmail OAuth refresh still sends secrets over HTTPS — tests cover simulate path only.
- Executor live Stripe/Shopify still require explicit `dry_run=False` + env keys; no
  additional env-level dry-run interlock was added this pass.

## Verification checklist

- [x] Commerce integration status JSON never contains `sk_`, `shpat_`, or refresh tokens
- [x] Stripe/Shopify client INFO/DEBUG logs never contain API keys during mocked live calls
- [x] Gmail simulate path rejects pending approvals and omits secrets from response/logs
- [x] Operator integrations API safe with credentials present in environment
