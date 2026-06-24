---
name: testing-marketmind-system
description: Deep system hardening for MarketMind after slice building completes. Use when proceed means test, improve, or rebuild—not a new feature slice.
---

# MarketMind System Hardening (Phase B)

Use when slice roadmap is complete and Aidan keeps saying **`proceed`**. Each turn is **one** hardening theme: test deeply, fix gaps, or rebuild broken parts.

## Read first

- `SLICE_WORKFLOW.md` § Phase B
- `docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md`
- `docs/qa/final_audit.md`
- `docs/issues/`

## Full system stack

```powershell
python -m ruff check .
python -m pytest -q
python scripts/local_ci.py
cd desktop; npm test; npm run build
```

With API running:

```powershell
uvicorn marketmind.api.app:app --host 127.0.0.1 --port 8000
$env:MARKETMIND_API_BASE="http://127.0.0.1:8000"
python scripts/verify_marketmind_deploy.py
python scripts/check_operator_readiness.py --api
```

## Hardening rotation (pick one per proceed)

1. **Approval gate** — pending approvals never execute; dry_run defaults
2. **Operator health** — preflight, readiness, snapshot gaps, warnings parse correctly
3. **Overview navigation** — audit every metric/link has Vitest; add missing tests
4. **Experiment lifecycle** — rules, snapshots, trends, daily report math
5. **Commerce adapters** — Stripe/Shopify/Gmail fakes; no secrets in logs
6. **Deploy/CI** — `.github/workflows/ci.yml`, `local_ci.py`, deploy verify job
7. **Docs drift** — OPERATING_INDEX, OWNER_MANUAL, runbooks match code

## Evidence

Every hardening pass gets `docs/engineering_log/YYYY-MM-DD-<slug>.md` even if only tests/docs changed. Append `reports/local_ci/TEST_LOG.md` via `local_ci.py`.

## Output format

Report to Aidan:

- Theme tested
- Commands run + exit codes
- Gaps found (file:line or test name missing)
- Fixes merged or filed in `docs/issues/`

## Never

- Add feature slices during Phase B unless Aidan redirects
- Weaken tests to green
- Skip logging because "only tested"
