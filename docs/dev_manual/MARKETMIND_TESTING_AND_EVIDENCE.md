# MarketMind Testing And Evidence Manual

**Adapted from:** Futures Trading Bot `docs/dev_manual/FUTURES_TESTING_AND_EVIDENCE.md`
(trading-specific sections removed; commerce/approval gate substituted).

**Last updated:** 2026-06-24

---

## Safe default stack (every slice)

```powershell
python -m ruff check .
python -m pytest -q
cd desktop; npm test; npm run build
python scripts/local_ci.py
```

Run focused tests first when changing a narrow area.

---

## Test inventory (approximate)

| Layer | Location | Count (approx) |
|---|---|---|
| Backend | `tests/test_*.py` | **465** pytest cases |
| Desktop | `desktop/src/**/*.test.ts(x)` | **23** Vitest files |
| CI | `.github/workflows/ci.yml` | ruff + pytest + deploy smoke + desktop build/test |

---

## Focused backend commands

```powershell
python -m pytest -q tests/test_operator_health.py tests/test_operator_readiness.py
python -m pytest -q tests/test_api.py tests/test_approvals.py
python -m pytest -q tests/test_experiment_rules.py tests/test_snapshots.py
python -m pytest -q tests/test_deploy_verify.py
python -m pytest -q tests/test_runner.py
```

## Focused desktop commands

```powershell
cd desktop
npm test -- src/components/OperatorHealthPanel.test.tsx
npm test -- src/dailyReportNavigation.test.ts
npm test -- src/components/OverviewReportPrimaryMetrics.test.tsx
```

If an area has no focused test, **add one in the same PR** as the behavior change.

---

## Operator / deploy evidence (read-only)

```powershell
uvicorn marketmind.api.app:app --reload
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/operator/preflight
curl -s "http://127.0.0.1:8000/operator/health-panel?date=2026-06-23"
python scripts/check_operator_readiness.py --api
python scripts/verify_marketmind_deploy.py
```

With API running locally:

```powershell
$env:MARKETMIND_API_BASE="http://127.0.0.1:8000"
python scripts/verify_marketmind_deploy.py
python scripts/check_operator_readiness.py --api
```

---

## Microscope checklist (per slice)

- [ ] Regression test names the failure mode (comment or test name)
- [ ] Happy path + at least one edge (missing handler, zero count, empty list)
- [ ] Desktop test if UI changed; API test if endpoint changed
- [ ] No secrets in test output
- [ ] `ruff` + full `pytest` green
- [ ] Engineering log entry with command output
- [ ] CHANGELOG slice entry

---

## Test log format

Append to `reports/local_ci/TEST_LOG.md` (via `scripts/local_ci.py`) or paste in PR:

```text
Timestamp: (UTC)
Branch:
Commit:
Environment: Python x.y, Node x.y
Commands:
  - ... → exit 0 (Ns)
Result: PASS | FAIL
Failure output: (snippet or "none")
Follow-up:
```

---

## Phase B — system hardening passes

When slice building is complete, each `proceed` runs a **hardening theme**:

1. **Approval gate** — `tests/test_approvals.py`, `tests/test_commerce_approval_policy.py`
2. **Operator surfaces** — health panel, readiness, preflight, snapshot gaps
3. **Overview navigation** — every metric/link has Vitest coverage
4. **Deploy path** — `verify_marketmind_deploy`, CI deploy-verify job
5. **Commerce dry-run** — Stripe/Shopify adapters never live without approval
6. **Experiment math** — rules, snapshots, trend summary, daily report

Record each pass in `docs/engineering_log/` even if no code changed (document gaps).

---

## Do not

- Weaken tests to go green
- Skip desktop tests because "npm wasn't in PATH" without logging the gap
- Merge without engineering log entry for significant changes
- Trust deploy without manifest/API verification
