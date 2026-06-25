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
# API smoke (uvicorn running):
python scripts/local_ci.py --full
```

`--full` runs `verify_marketmind_deploy.py` and `check_operator_readiness.py --api`
(matching the GitHub `deploy-verify` job). Requires `MARKETMIND_API_BASE`.

Run focused tests first when changing a narrow area.

---

## Test inventory (approximate)

| Layer | Location | Count (approx) |
|---|---|---|
| Backend | `tests/test_*.py` | **860** pytest cases |
| Desktop | `desktop/src/**/*.test.ts(x)` | **29** Vitest files |
| CI | `.github/workflows/ci.yml` | ruff + pytest + deploy smoke + desktop build/test |
| Docs drift | `tests/test_docs_drift.py`, `test_docs_drift_hardening.py`, `test_docs_drift_contract.py` | env names, suite counts, rotation 3 contract parity |

Minimum counts are also defined in `marketmind/docs_contract.py`.

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
curl -s http://127.0.0.1:8000/operator/readiness
curl -s http://127.0.0.1:8000/operator/integrations
python scripts/check_operator_readiness.py --api
python scripts/verify_marketmind_deploy.py
```

`verify_marketmind_deploy.py` checks the same four endpoints as CI (`deploy_ci_contract.py`):
`/health`, `/operator/health-panel`, `/operator/readiness`, `/operator/integrations`
(secret-free JSON — no `sk_test_`, `shpat_`, etc.).

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

When slice building is complete, each `proceed` runs a **hardening theme** (see
`.agents/skills/testing-marketmind-system/SKILL.md`):

1. **Approval gate** — pending never executes; `dry_run` defaults
2. **Operator health** — preflight, readiness, snapshot gaps, health panel parsers
3. **Overview navigation** — Vitest coverage for metrics and links
4. **Experiment lifecycle** — rules, snapshots, trends, daily report math
5. **Commerce adapters** — Stripe/Shopify/Gmail fakes; no secrets in logs
6. **Deploy/CI** — `local_ci.py` parity with `.github/workflows/ci.yml`
7. **Docs drift** — `OWNER_MANUAL`, `OPERATING_INDEX`, testing manual vs code

**Rotation 2** (passes 8–14) adds contract modules and hardening test files per theme
(e.g. `deploy_ci_contract.py`, `test_docs_drift_hardening.py`). See engineering logs
`2026-06-24-*-r2.md`.

**Rotation 3** (passes 15–21) deepens contracts with dedicated `test_*_contract.py`
modules per theme and UI/API parity guards:

| Pass | Theme | Contract module | Contract tests |
|---|---|---|---|
| 15 | Approval gate | `approval_gate_contract.py` | `test_approval_gate_contract.py` |
| 16 | Operator health | `operator_health_contract.py` | `test_operator_health_contract.py` |
| 17 | Overview navigation | `overview_navigation_contract.py` | `test_overview_navigation_contract.py` |
| 18 | Experiment lifecycle | `experiment_lifecycle_contract.py` | `test_experiment_lifecycle_contract.py` |
| 19 | Commerce adapters | `commerce_adapters_contract.py` | `test_commerce_adapters_contract.py` |
| 20 | Deploy/CI | `deploy_ci_contract.py` | `test_deploy_ci_contract.py` |
| 21 | Docs drift | `docs_contract.py` | `test_docs_drift_contract.py` |

See engineering logs `2026-06-24-*-r3.md`. Drift guards:
`test_docs_drift.py`, `test_docs_drift_hardening.py`, `test_docs_drift_contract.py`.

**Rotation 4** (passes 22–28) deepens rotation 3 contracts with API path matrices,
UI label parity, and extended failure-edge guards:

| Pass | Theme | Contract module | Contract tests |
|---|---|---|---|
| 22 | Approval gate | `approval_gate_contract.py` | `test_approval_gate_contract.py` |
| 23 | Operator health | `operator_health_contract.py` | `test_operator_health_contract.py` |
| 24 | Overview navigation | `overview_navigation_contract.py` | `test_overview_navigation_contract.py` |
| 25 | Experiment lifecycle | `experiment_lifecycle_contract.py` | `test_experiment_lifecycle_contract.py` |
| 26 | Commerce adapters | `commerce_adapters_contract.py` | `test_commerce_adapters_contract.py` |
| 27 | Deploy/CI | `deploy_ci_contract.py` | `test_deploy_ci_contract.py` |
| 28 | Docs drift | `docs_contract.py` | `test_docs_drift_contract.py` |

See engineering logs `2026-06-24-*-r4.md`.

Record each pass in `docs/engineering_log/` even if only tests/docs changed.

---

## Do not

- Weaken tests to go green
- Skip desktop tests because "npm wasn't in PATH" without logging the gap
- Merge without engineering log entry for significant changes
- Trust deploy without manifest/API verification
