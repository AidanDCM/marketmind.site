# Changelog

---

## 2026-06-24 — Phase B pass 37: Operator health hardening (rotation 6)

### Hardening: snapshot-gaps empty date 422, run-cycle edges, CLI pending blocker

- **`operator.py`** — reject empty `date=` on `GET /operator/snapshot-gaps` (parity with health-panel/readiness).
- **`operator_health_contract.py`** — run-cycle/last-cycle paths, integrations subkeys, UI button labels.
- **`test_operator_health_contract.py`** — +11 tests: 422 edges, pending blocker API/CLI, integrations keys.
- **`OperatorHealthPanel.test.tsx`** — +1 test: `Snapshots for` date header when gaps exist.

---

## 2026-06-24 — Phase B pass 36: Approval gate hardening (rotation 6)

### Hardening: approve/deny 404 edges, badge map SSOT, Deny button Vitest

- **`approval_gate_contract.py`** — note body key, path suffixes, status badge class map.
- **`test_approval_gate_contract.py`** — +9 tests: approve/deny 404, cross-transition 409, badge parity.
- **`ApprovalQueue.test.tsx`** — +1 test: Deny calls `denyRecord`.

---

## 2026-06-24 — Phase B pass 35: Docs drift hardening (rotation 5)

### Hardening: rotation 5 contract SSOT, vitest inventory guards, engineering-log parity

- **`docs_contract.py`** — `PHASE_B_ROTATION_5_CONTRACTS`, pass 29–35 constants; `MIN_PYTEST_CASES` → 935.
- **`test_docs_drift_contract.py`** — +18 tests: rotation 5 file parity, pass 35 status, operating index.
- **`MARKETMIND_TESTING_AND_EVIDENCE.md`** — Passes 29–35 contract table; rotation 5 complete.

---

## 2026-06-24 — Phase B pass 34: Deploy/CI hardening (rotation 5)

### Hardening: readiness/integrations fetch failures, health keys, workflow job parity

- **`deploy_ci_contract.py`** — health response keys, uvicorn target, job names, verify module path.
- **`test_deploy_ci_contract.py`** — +7 tests: fetch error prefixes, health keys, workflow script parity.

---

## 2026-06-24 — Phase B pass 33: Commerce adapters hardening (rotation 5)

### Hardening: import batch 404, readiness commerce keys, Shopify products pull, ad CSV wiring

- **`commerce_adapters_contract.py`** — batch-not-found detail, readiness commerce key, Shopify products label, source query.
- **`test_commerce_adapters_contract.py`** — +7 tests: 404/409 edges, client parity, readiness commerce keys.
- **`LiveData.test.tsx`** — +1 test: Import CSV calls `importAdCsv`.

---

## 2026-06-24 — Phase B pass 32: Experiment lifecycle hardening (rotation 5)

### Hardening: status/note 404 edges, portfolio keys, notes UI wiring

- **`experiment_lifecycle_contract.py`** — router path, validation fragments, portfolio/active entry keys, notes UI labels.
- **`test_experiment_lifecycle_contract.py`** — +9 tests: 404/422 edges, portfolio keys, status round-trip, notes empty-list behavior.
- **`ActiveExperiments.test.tsx`** — +1 test: Add note calls `addExperimentNote`.

---

## 2026-06-24 — Phase B pass 31: Overview navigation hardening (rotation 5)

### Hardening: trend as_of ISO 422, days max edge, daily-report date query, health-panel snapshots

- **`overview_navigation_contract.py`** — router paths, trend validation details, response keys, UI labels.
- **`test_overview_navigation_contract.py`** — +10 tests: invalid as_of/days 422, client date query, preference helpers, response keys.
- **`Overview.test.tsx`** — +1 test: health panel View snapshots through Overview parent.

---

## 2026-06-24 — Phase B pass 30: Operator health hardening (rotation 5)

### Hardening: snapshot-gaps API edges + readiness date 422 + health-panel UI parity

- **`operator_health_contract.py`** — router paths, checklist keys, empty-date detail, UI labels.
- **`test_operator_health_contract.py`** — +10 tests: snapshot-gaps date scope, readiness 422, last-cycle empty, preflight `operator_log_exists`, desktop query params, UI parity.
- **`OperatorHealthPanel.test.tsx`** — +2 tests: `Run cycle now` invokes `onRunCycle`.

---

## 2026-06-24 — Phase B pass 29: Approval gate hardening (rotation 5)

### Hardening: approval CRUD API paths + transition 409 edges + queue approve wiring

- **`approval_gate_contract.py`** — router paths, UI button labels, filter storage key, transition fragments.
- **`test_approval_gate_contract.py`** — +14 tests: list/get/pending, 409 transitions, execute-all, UI parity.
- **`ApprovalQueue.test.tsx`** — +1 test: Approve calls `approveRecord`.

---

## 2026-06-24 — Phase B pass 28: Docs drift hardening (rotation 4)

### Hardening: rotation 4 contract table + vitest inventory guards + engineering-log parity

- **`docs_contract.py`** — `PHASE_B_ROTATION_4_CONTRACTS`, pass 22–28 constants; `MIN_PYTEST_CASES` → 860.
- **`test_docs_drift_contract.py`** — +23 tests: rotation 4 file parity, operating index pass 28, vitest guards.
- **`MARKETMIND_TESTING_AND_EVIDENCE.md`** — passes 22–28 contract table.

---

## 2026-06-24 — Phase B pass 27: Deploy/CI hardening (rotation 4)

### Hardening: workflow boot constants + verify failure matrix + local_ci log helpers

- **`deploy_ci_contract.py`** — CI node/DB/uvicorn constants, deploy failure prefixes, local_ci paths.
- **`test_deploy_ci_contract.py`** — +18 tests: workflow parity, verify failure edges, token forwarding.

---

## 2026-06-24 — Phase B pass 26: Commerce adapters hardening (rotation 4)

### Hardening: import/ad API paths + integration key whitelists + LiveData pull wiring

- **`commerce_adapters_contract.py`** — import history/ad paths, Stripe/Shopify keys, LiveData UI labels.
- **`test_commerce_adapters_contract.py`** — +19 tests: 409 safe-fail matrix, ad CSV 422, mask vectors, UI parity.
- **`LiveData.test.tsx`** — +1 test: Pull Now triggers Stripe import.

---

## 2026-06-24 — Phase B pass 25: Experiment lifecycle hardening (rotation 4)

### Hardening: per-experiment API paths + ActiveExperiments UI parity + status/note 422 edges

- **`experiment_lifecycle_contract.py`** — detail suffixes, status filters, UI labels, preference keys.
- **`test_experiment_lifecycle_contract.py`** — +16 tests: client/router parity, 404/422 edges, note round-trip.
- **`ActiveExperiments.test.tsx`** — +1 test: reactivate ended experiment.

---

## 2026-06-24 — Phase B pass 24: Overview navigation hardening (rotation 4)

### Hardening: trend query params + lookback validation + health-panel attention link

- **`overview_navigation_contract.py`** — trend API path/query params, UI labels, daily-cycle path.
- **`test_overview_navigation_contract.py`** — +14 tests: 422 edges, lookback days matrix, attention_only.
- **`Overview.test.tsx`** — +1 test: health panel Show attention through parent.

---

## 2026-06-24 — Phase B pass 23: Operator health hardening (rotation 4)

### Hardening: extended API paths + readiness date query + Gmail secret warning

- **`operator_health_contract.py`** — desktop/extended API paths, query params, banner action labels.
- **`test_operator_health_contract.py`** — +13 tests: integrations panel, date-scoped readiness, Gmail secret.
- **`OperatorHealthPanel.test.tsx`** — pending blocker list links to approval queue.

---

## 2026-06-24 — Phase B pass 22: Approval gate hardening (rotation 4)

### Hardening: approval API paths + HIGH_RISK approved matrix + queue filter UI

- **`approval_gate_contract.py`** — approval/execute API paths, filter options, UI status gates.
- **`test_approval_gate_contract.py`** — +29 tests: approved HIGH_RISK matrix, approve/deny API, execute log.
- **`ApprovalQueue.test.tsx`** — +2 tests: filter bar parity, `already_executed` message.

---

## 2026-06-24 — Phase B pass 21: Docs drift hardening (rotation 3)

### Hardening: docs_contract rotation 3 table + test_docs_drift_contract

- **`docs_contract.py`** — rotation 3 contract triples, drift test files, inventory doc paths.
- **`test_docs_drift_contract.py`** — 20 tests: rotation 3 module/test parity, operator doc guards.
- **`MARKETMIND_TESTING_AND_EVIDENCE.md`** — passes 15–21 contract table; AGENTS/SLICE_WORKFLOW drift refs.

---

## 2026-06-24 — Phase B pass 20: Deploy/CI hardening (rotation 3)

### Hardening: deploy_ci_contract step/env constants + verify failure formatter

- **`deploy_ci_contract.py`** — local-ci step names, deploy env vars, failure/success lines, formatter.
- **`deploy_verify.py`** — wired to contract constants and `format_integrations_leak_failure`.
- **`test_deploy_ci_contract.py`** — 21 tests: workflow parity, leak-marker matrix, endpoint smoke, docs.

---

## 2026-06-24 — Phase B pass 19: Commerce adapters hardening (rotation 3)

### Hardening: commerce_adapters_contract API paths + deploy leak-marker parity

- **`commerce_adapters_contract.py`** — handler actions, read/execute/source/import API paths,
  deploy leak markers, Gmail integration keys, CLI path.
- **`test_commerce_adapters_contract.py`** — 20 tests: mask parity with deploy markers,
  handler/policy matrix, integrations secret-free, Shopify execute/log API, sources 409.

---

## 2026-06-24 — Phase B pass 18: Experiment lifecycle hardening (rotation 3)

### Hardening: lifecycle API contract + report suffix matrix + ActiveExperiments checklist

- **`experiment_lifecycle_contract.py`** — API paths, pending-lesson formatter, lesson regex pattern.
- **`test_experiment_lifecycle_contract.py`** — 11 tests: refund/ATC suffixes, API smoke, evaluate kill, attention rulings.
- **`reports.py`** — pending lesson uses `format_pending_approvals_lesson`.
- **`ActiveExperiments.test.tsx`** — +3 tests: scale attention filter, checklist, mistakes sections.

---

## 2026-06-24 — Phase B pass 17: Overview navigation hardening (rotation 3)

### Hardening: overview_navigation_contract + parent-level metric/recommendation links

- **`overview_navigation_contract.py`** — Overview API paths, localStorage keys, lookback options.
- **`test_overview_navigation_contract.py`** — 12 tests: desktop client parity, API smoke, lifecycle phrases.
- **`Overview.test.tsx`** — +7 integration tests: live data, scale queue, score product, lessons, contribution profit.

---

## 2026-06-24 — Phase B pass 16: Operator health hardening (rotation 3)

### Hardening: operator_health_contract formatters + regex/desktop parity

- **`operator_health_contract.py`** — blocker/snapshot formatters, regex patterns, API paths, warning prefixes.
- **`operator_preflight.py` / `operator_health.py`** — wired to contract formatters.
- **`test_operator_health_contract.py`** — 14 tests: desktop regex parity, API paths, kill ruling blockers, CLI `--strict`.
- **`OperatorHealthPanel.test.tsx`** — experiment ruling blocker links to View experiment.

---

## 2026-06-24 — Phase B pass 15: Approval gate hardening (rotation 3)

### Hardening: approval_gate_contract SSOT + full action-set matrix

- **`approval_gate_contract.py`** — BLOCKED/HIGH_RISK/AUTO_ALLOWED sets, handler names, refusal fragments.
- **`commerce_approval_policy.py`** — imports action sets from contract; `complete` status alias.
- **`test_approval_gate_contract.py`** — 45 tests: disjoint sets, HIGH_RISK/AUTO/BLOCKED matrix, API/executor parity.
- **`ApprovalQueue.test.tsx`** — blocked records hide approve/deny/execute.

---

## 2026-06-24 — Phase B pass 14: Docs drift hardening (rotation 2)

### Hardening: deploy-verify doc parity + stale inventory guards

- **`docs_contract.py`** — stale pytest/Vitest inventory lists, `DEPLOYMENT_DOC_PATH`.
- **`test_docs_drift_hardening.py`** — 7 tests: verify endpoints in DEPLOYMENT/testing manual,
  integrations secret-leak docs, Phase B rotation 2, no stale 512/567 counts in operator docs.
- **`DEPLOYMENT.md`**, **`MARKETMIND_TESTING_AND_EVIDENCE.md`**, **`OWNER_MANUAL.md`** — integrations verify.

---

## 2026-06-24 — Phase B pass 13: Deploy/CI hardening (rotation 2)

### Hardening: deploy verify integrations + CI workflow contract

- **`deploy_ci_contract.py`** — verify endpoints, scripts, workflow job names, leak markers.
- **`deploy_verify.py`** — checks `/operator/integrations` for forbidden secret substrings.
- **`test_deploy_ci_hardening.py`** — CI workflow parity with `local_ci` and contract endpoints.

---

## 2026-06-24 — Phase B pass 12: Commerce adapters hardening (rotation 2)

### Hardening: secret mask contract + commerce API/CLI parity

- **`commerce_adapters_contract.py`** — mask vectors, action aliases, canonical env names.
- **`test_commerce_adapters_hardening.py`** — +10 tests: aliases, admin token, readiness/health,
  execute/log API, `check_commerce_config.py` subprocess.
- **`commerce_integrations.py` / `commerce_approval_policy.py`** — wired to contract.

---

## 2026-06-24 — Phase B pass 11: Experiment lifecycle hardening (rotation 2)

### Hardening: report string contract + lifecycle API/UI parity

- **`experiment_lifecycle_contract.py`** — canonical daily-report phrases and attention rulings.
- **`test_experiment_lifecycle_hardening.py`** — TS/Python cross-check, report emission,
  active/trend ruling parity, `attention_only` filter, ended-experiment exclusion.
- **`ActiveExperiments.test.tsx`** — attention/status filters, focus card, chart, end experiment.

---

## 2026-06-24 — Phase B pass 10: Overview navigation hardening (rotation 2)

### Hardening: parent-level Overview integration coverage

- **`Overview.test.tsx`** — run cycle, readiness/health/metrics/report navigation,
  date/lookback refetch, and attention-only empty state exercised through `Overview.tsx`
  wiring (child components already covered in isolation).

---

## 2026-06-24 — Phase B pass 9: Operator health hardening (rotation 2)

### Hardening: warning string contract + readiness/preflight API paths

- **`operator_health_contract.py`** — canonical warning strings shared with desktop parsers.
- **`test_operator_health_hardening.py`** — Gmail live-writes warning, pending blockers,
  readiness API strict mode, health-panel preflight parity, TS/Python constant cross-check.
- **`OperatorMessageListItem.test.tsx`** — operator log warning renders without action button.

---

## 2026-06-24 — Phase B pass 8: Approval gate hardening (rotation 2)

### Hardening: full BLOCKED_ACTIONS matrix + API batch/idempotency

- **`test_approval_gate_hardening.py`** — parametrized refusal for every `BLOCKED_ACTIONS`
  entry; execute-all captures blocked rows; API denied/idempotent/batch/live-refusal paths.
- **`ApprovalQueue.test.tsx`** — denied records show no Execute or Approve controls.

---

## 2026-06-24 — Phase B pass 7: Docs drift hardening

### Hardening: operator docs match code and suite inventory

- **`marketmind/docs_contract.py`** — canonical env var names and minimum test counts.
- **`tests/test_docs_drift.py`** — regression tests for OWNER_MANUAL env table, suite
  inventory, deploy verifier parity, and `local_ci --full` documentation.
- **Docs updated** — `OWNER_MANUAL.md`, `AGENTS.md`, `SLICE_WORKFLOW.md`,
  `MARKETMIND_TESTING_AND_EVIDENCE.md`, `docs/DEPLOYMENT.md`, `OPERATING_INDEX.md`.

---

## 2026-06-24 — Phase B pass 6: Deploy/CI hardening

### Hardening: local_ci parity with GitHub Actions deploy-verify job

- **`local_ci --full`** — now runs `check_operator_readiness.py --api` after deploy verify,
  matching `.github/workflows/ci.yml`.
- **`CI_DEPLOY_VERIFY_SCRIPTS`** — documented parity contract; regression tests assert scripts
  exist and appear in the workflow file.
- **Deploy verify** — TestClient integration test, unreachable health/panel cases, warnings-only
  pass semantics.

---

## 2026-06-24 — Phase B pass 5: Commerce adapters hardening

### Hardening: Stripe/Shopify/Gmail fakes; no secrets in logs or API

- **`test_commerce_adapters_hardening.py`** — readiness snapshots, simulate responses, and
  client DEBUG logs never echo credentials; Gmail pending approval rejected.
- **Executor** — live Shopify mock path and Gmail simulate path regression: tokens never
  appear in `ExecutionResult.to_dict()`.
- **API** — `GET /operator/integrations` with credentials in env returns booleans only.

---

## 2026-06-24 — Phase B pass 4: Experiment lifecycle hardening

### Hardening: daily report math, trend direction, rules priority

- **`generate_daily_report`** — low add-to-cart risk, ROAS lessons, ATC aggregation regressions.
- **`build_experiment_trend_summary`** — CAC down/flat, active-without-snapshots, scale attention.
- **`evaluate_experiment`** — kill ruling wins when kill and pause signals both present.
- **API** — `/report/daily` and `/experiment/trend-summary` integration tests with snapshots.
- **Desktop** — `dailyReportNavigation` parses exact backend ATC risk and healthy ROAS lesson text.

---

## 2026-06-24 — Phase B pass 3: Operator health hardening

### Hardening: health warnings match desktop parsers

- **`build_operator_health`** — regression tests for snapshot-gap warnings (incl. truncated
  ID lists), Gmail secret, and Shopify live-write warnings.
- **API** — `/operator/health-panel` returns missing-snapshot warning when active experiments
  lack a snapshot for the requested date.
- **Desktop parsers** — Gmail secret, Shopify prefix, truncated snapshot gaps; preflight partial
  actions; health panel warning row wiring.

---

## 2026-06-24 — Phase B pass 2: Approval gate hardening

### Hardening: pending never executes; dry_run defaults enforced

- **Commerce policy / executor / API** — regression tests for blocked actions, alias
  normalization, pending status variants, execute-all batch skipping pending rows.
- **`ApprovalQueue.test.tsx`** — pending shows Approve/Deny only; approved Execute always
  passes `dry_run=true`.
- **`client.test.ts`** — `executeApproved()` omits live flag by default.

---

## 2026-06-24 — Phase B pass 1: Overview navigation Vitest audit

### Hardening: parent-level Overview navigation tests

- **`Overview.test.tsx`** — mocked API integration tests for header Snapshots, pending
  approval banner, trend attention link, Chart/Details/Record row actions, and no-report
  empty state wiring (gaps not covered by child component tests alone).
- **CI fix** — `lookbackOptions.ts` docstring syntax and `ActiveExperiments.tsx`
  `StatusBadge` declaration (blocked frontend typecheck on main).

---

## 2026-06-24 — Slice 119: No-report empty Score Product link

### Slice 119: Jump from empty daily report to Score Product

- **`OverviewReportEmptyState`** — no report data shows **Score a product** alongside record snapshot.

---

## 2026-06-24 — Slice 118: Trend attention empty link

### Slice 118: Jump from empty attention-only trends to Active Experiments

- **`OverviewTrendEmptyState`** — when attention filter shows no rows, **View all experiments** opens Active Experiments.

---

## 2026-06-24 — Slice 117: Conversion zero-order link

### Slice 117: Jump from zero-order conversion to Active Experiments

- **`overviewReportSecondaryMetrics.ts`** — conversion links when ad spend > 0 and zero orders.
- **Overview secondary metrics** — **Conversion** opens Active Experiments in that funnel-failure case.

---

## 2026-06-24 — Slice 116: Secondary metrics risk links

### Slice 116: Jump from elevated refund / low add-to-cart to Active Experiments

- **`overviewReportSecondaryMetrics.ts`** — threshold helpers aligned with daily report risks.
- **Overview secondary metrics** — refund rate (≥5%) and low add-to-cart (spend, zero orders) open Active Experiments.

---

## 2026-06-24 — Process: Testing discipline and engineering log

### Futures Bot patterns applied to MarketMind (not a feature slice)

- **`SLICE_WORKFLOW.md`** — Phase A slices vs Phase B hardening; microscope testing; engineering log required.
- **`docs/engineering_log/`** — per-entry forensic ledger (why/where/when/verification).
- **`docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md`** — command reference (~465 pytest + desktop Vitest).
- **`scripts/local_ci.py`** — offline CI + append-only `reports/local_ci/TEST_LOG.md`.
- **`.agents/skills/testing-marketmind-slice|system`** — agent instructions for slice vs hardening work.
- **`AGENTS.md` / `OPERATING_INDEX.md`** — updated binding rules.

---

## 2026-06-23 — Slice 115: Overview CAC Active Experiments link

### Slice 115: Jump from daily report CAC to Active Experiments

- **`OverviewReportPrimaryMetrics`** — daily report **CAC** metric opens Active Experiments.

---

## 2026-06-23 — Slice 114: Overview revenue Live Data link

### Slice 114: Jump from daily report revenue to Live Data

- **`OverviewReportPrimaryMetrics`** — daily report **Revenue** metric opens Live Data.

---

## 2026-06-23 — Slice 113: Overview contribution profit link

### Slice 113: Jump from daily report contribution profit to Active Experiments

- **`OverviewReportSecondaryMetrics`** — daily report **Contribution Profit** metric opens Active Experiments.

---

## 2026-06-23 — Slice 112: Overview orders Live Data link

### Slice 112: Jump from daily report orders to Live Data

- **`OverviewReportPrimaryMetrics`** — daily report **Orders** metric opens Live Data.

---

## 2026-06-23 — Slice 111: Overview ad spend import link

### Slice 111: Jump from daily report ad spend to Import History

- **`OverviewReportPrimaryMetrics`** — daily report **Ad Spend** metric opens Import History.

---

## 2026-06-23 — Slice 110: Readiness integration summary link

### Slice 110: Jump from readiness integration summary to Live Data

- **Operator readiness banner** — Gmail/Stripe/Shopify summary shows **Check Live Data**.

---

## 2026-06-23 — Slice 109: Snapshot gap experiment links

### Slice 109: Jump from missing snapshot rows to experiment details

- **Operator health panel** — each missing snapshot row shows **Details** to open that experiment.

---

## 2026-06-23 — Slice 108: Integration warning links

### Slice 108: Jump from live-write warnings to Live Data

- **`readinessBannerActions.ts`** — Gmail, Stripe, and Shopify live-write warnings link to Live Data.
- **Health panel and readiness banner** — integration warnings show **Check Live Data**.

---

## 2026-06-23 — Slice 107: Cycle and snapshot-complete links

### Slice 107: Jump from last cycle and complete snapshot gaps

- **Operator health panel** — last cycle shows **View experiments** when evaluations ran; complete snapshot summary shows **View snapshots**.

---

## 2026-06-23 — Slice 106: Generic daily report risk links

### Slice 106: Jump from portfolio-wide risks to Active Experiments

- **`dailyReportNavigation.ts`** — zero-order spend, refund-rate, and low-ATC risks link to Active Experiments; low ROAS lessons too.
- **Risks card** — shows **View experiments** on generic generated risk lines.

---

## 2026-06-23 — Slice 105: Generic daily report line shortcuts

### Slice 105: Link empty-portfolio and contribution recommendations

- **`dailyReportNavigation.ts`** — no-experiments recommendation → Score Product; positive contribution → Active Experiments; past lessons → library.
- **Recommendations and Lessons cards** — show navigation for generic generated lines.

---

## 2026-06-23 — Slice 104: Preflight summary shortcuts

### Slice 104: Jump from preflight summary to fix blockers

- **`preflightSummaryActions.ts`** — derives summary actions when preflight is not safe.
- **Operator health panel** — preflight summary shows **Open queue** and **Show attention** when applicable.

---

## 2026-06-23 — Slice 103: Missing ad spend import prompt

### Slice 103: Prompt to import ads when spend data is absent

- **Operator health panel** — warns when active experiments exist but no ad CSV is imported; **Import ads** opens Import History.

---

## 2026-06-23 — Slice 102: Daily report lesson shortcuts

### Slice 102: Jump from lesson lines to queue or Live Data

- **`dailyReportNavigation.ts`** — pending-approval and no-orders lesson text resolve to navigation targets.
- **Lessons card** — shows **Open queue** or **Check Live Data** on matching generated lesson lines.

---

## 2026-06-23 — Slice 101: Scale recommendation approval link

### Slice 101: Jump from scale recommendations to Approval Queue

- **`dailyReportNavigation.ts`** — scale recommendations (`submit scale request for approval`) resolve to queue navigation.
- **Recommendations card** — shows **Open queue** instead of **View experiment** for scale-ready products.

---

## 2026-06-23 — Slice 100: Daily report experiment links

### Slice 100: Jump from risks and recommendations to experiment details

- **`dailyReportNavigation.ts`** — maps `Product name: …` report lines to experiment ids.
- **`DailyReportInsightList`** — Risks and Recommendations cards show **View experiment** when a product matches trend/preflight data.

---

## 2026-06-23 — Slice 99: Integration metrics link to Live Data

### Slice 99: Jump from Gmail/Stripe/Shopify metrics to Live Data

- **Operator health panel** — Gmail, Stripe, and Shopify metric cards open the Live Data page.

---

## 2026-06-23 — Slice 98: Ad spend import history link

### Slice 98: Jump from imported ad spend to Import History

- **Operator health panel** — clickable **Imported ad spend** metric opens Import History when ad CSV data exists.

---

## 2026-06-23 — Slice 97: Overview lessons library link

### Slice 97: Jump from daily report lessons to Lessons library

- **`DailyReportLessonsCard`** — daily report lessons section with **View library** action.
- **Overview** — opens Lessons sidebar page from the report card.

---

## 2026-06-23 — Slice 96: Portfolio metric navigation in health panel

### Slice 96: Jump from Experiments and Lessons metrics

- **Operator health panel** — **Experiments** metric opens Active Experiments; **Lessons recorded** opens Lessons library.

---

## 2026-06-23 — Slice 95: Snapshot gaps header link

### Slice 95: Jump to Snapshot Recorder from health panel gaps

- **Operator health panel** — missing snapshot summary shows **Record snapshots**; opens recorder with date and first missing experiment pre-filled.

---

## 2026-06-23 — Slice 94: Pending approvals shortcuts in health panel

### Slice 94: Jump to approval queue from health metrics

- **Operator health panel** — new clickable **Pending approvals** metric when count > 0.
- **Last daily cycle** — “Open queue” link when the cycle queued approvals.

---

## 2026-06-23 — Slice 93: Link health panel warnings and blockers

### Slice 93: Operator health panel message shortcuts

- **`OperatorMessageListItem`** — shared list row with navigation links for known operator messages.
- **Operator health panel** — warnings and preflight blockers link to approvals, experiments, or snapshots (same as readiness banner).

---

## 2026-06-23 — Slice 92: Refresh nav badges after daily cycle

### Slice 92: Sidebar counts update when operator daily cycle completes

- **`overviewDailyCycle.ts`** — shared run-cycle + refetch helper; fires `onCycleComplete` only on success.
- **Overview** — bumps `navRefresh` after daily cycle so approval and attention badges refresh immediately.

---

## 2026-06-23 — Slice 91: Link readiness banner blockers

### Slice 91: Operator readiness banner shortcuts to fix blockers

- **`readinessBannerActions.ts`** — maps preflight blocker and snapshot-gap warning text to navigation targets.
- **Operator readiness banner** — pending approvals, experiment rulings, and missing snapshots link to the right page.

---

## 2026-06-23 — Slice 90: Persist Overview selected date

### Slice 90: Remember Overview date picker across sessions

- **`overviewPreferences.ts`** — persists selected Overview date in `localStorage`; rejects future or invalid values.
- **Overview** — restores saved date on load and writes changes back to storage.

---

## 2026-06-23 — Slice 89: Overview data refresh and preflight experiment links

### Slice 89: Refresh Overview after operator actions; link preflight attention rows

- **Overview** — refetches health/trends when `dataRevision` bumps (e.g. after recording a snapshot).
- **Operator health panel** — preflight attention rows and “Need attention” metric open Active Experiments.

---

## 2026-06-23 — Slice 88: Snapshot gap shortcuts and nav refresh

### Slice 88: Record missing snapshots from health panel; refresh badges after submit

- **Operator health panel** — missing snapshot list links to Snapshot Recorder (date + experiment pre-filled).
- **Snapshot Recorder** — calls back after successful submit so sidebar attention counts refresh immediately.

---

## 2026-06-23 — Slice 87: Overview links to Snapshots with date prefill

### Slice 87: Jump from Overview to Snapshot Recorder

- **Overview** — Snapshots button beside date picker; stale trend rows and empty state link to recorder.
- **Snapshot Recorder** — accepts navigation context for `snapshot_date` and optional `experiment_id`.

---

## 2026-06-23 — Slice 86: Persist Active Experiments status filter

### Slice 86: Remember all / active / ended filter on Active Experiments

- **`activeExperimentsPreferences.ts`** — persists status filter (`all` / `active` / `ended`) in `localStorage`.
- Focusing a specific experiment still switches to **all** for that navigation visit.

---

## 2026-06-23 — Slice 85: Persist approval filter and badge deep-link

### Slice 85: Remember Approval Queue filter; badge opens first pending item

- **`approvalQueuePreferences.ts`** — persists queue status filter in `localStorage`.
- **`usePendingApprovalSummary`** — returns pending count plus first `approval_id` for deep links.
- **Nav approval badge** — opens queue with first pending card focused (matches Overview banner).

---

## 2026-06-23 — Slice 84: Focus pending approval and refresh nav badges

### Slice 84: Deep-link to first pending approval; immediate sidebar counts

- **Overview banner** — opens Approval Queue with the first pending card expanded and scrolled into view.
- **Approval Queue** — supports `focusApprovalId` navigation context.
- **Nav badges** — refresh immediately after approval actions or experiment status changes (not only on 15s poll).

---

## 2026-06-23 — Slice 83: Persist Active Experiments attention filter

### Slice 83: Remember attention filter; richer pending-approval banner

- **`activeExperimentsPreferences.ts`** — persists “Needs attention” on Active Experiments (`localStorage`).
- **Overview** — pending-approval banner shows first item summary (e.g. action name).
- **`pendingApprovalBannerText`** — shared banner copy helper with tests.

---

## 2026-06-23 — Slice 82: Overview alerts link out; highlight attention cards

### Slice 82: Clickable Overview warnings and matching experiment highlights

- **Overview** — pending-approvals banner opens Approval Queue; “need attention” opens filtered Active Experiments.
- **Active Experiments** — red-tint cards for kill/pause/scale or CAC above break-even (matches Overview trend rows).
- **`experimentCardNeedsHighlight`** — shared highlight rule.

---

## 2026-06-23 — Slice 81: Approval badge and attention-filter navigation

### Slice 81: Nav badges link to filtered views

- **`usePendingApprovalCount`** — yellow badge on Approval Queue when pending items exist.
- **Active Experiments badge click** — opens page with “Needs attention” filter enabled.
- **Active Experiments** — “Needs attention” checkbox; shared `experimentAttention` helper.

---

## 2026-06-23 — Slice 80: Active Experiments nav attention badge

### Slice 80: Surface experiment attention count in sidebar

- **`useExperimentAttentionCount`** — polls `GET /experiment/portfolio` when API is connected.
- **Sidebar** — red badge on Active Experiments when `needs_attention > 0`.
- **Active Experiments Chart** — uses saved Overview lookback preference instead of fixed 30d.

---

## 2026-06-23 — Slice 79: Shared lookback bounds and 60/90d Overview

### Slice 79: Align snapshot-trend API and Overview with 1–90 day lookback

- **`marketmind/lookback.py`** — shared `normalize_lookback_days` (1–90) for trend endpoints.
- **`GET /snapshots/trend/{id}`** — rejects out-of-range `days` with 422.
- **Overview** — lookback selector adds 60d and 90d; shared `lookbackOptions.ts` with Trend page.

---

## 2026-06-23 — Slice 78: Trend-summary day bounds and Chart from Active Experiments

### Slice 78: Cap trend lookback at 90 days; Chart shortcut on experiment cards

- **`normalize_trend_summary_days`** — shared 1–90 validation for `GET /experiment/trend-summary`.
- **Active Experiments** — Chart button opens Trend page with experiment pre-filled (30d).
- **CI deploy-verify** — also runs `check_operator_readiness.py --api` after deploy smoke.

---

## 2026-06-23 — Slice 77: Overview trend row navigation

### Slice 77: Jump from Overview to Trend chart or experiment details

- **`navigation.ts`** — shared `Page` and `PageContext` types for cross-page handoff.
- **Overview** — Chart / Details buttons on each CAC trend row.
- **Trend & Active Experiments** — accept navigation context (pre-filled experiment, auto-load / expand).

---

## 2026-06-23 — Slice 76: API mode for readiness CLI

### Slice 76: Check readiness against a running API

- **`fetch_operator_readiness_from_api`** — urllib GET helper for `GET /operator/readiness`.
- **`scripts/check_operator_readiness.py`** — `--api` uses `MARKETMIND_API_BASE` / `MARKETMIND_API_TOKEN`; `--date` for snapshot gaps.

---

## 2026-06-23 — Slice 75: Configurable trend lookback on Overview

### Slice 75: 7/14/30-day CAC trend window

- **`overviewPreferences.ts`** — shared localStorage helpers for Overview trend controls.
- **Desktop Overview** — lookback selector (7d / 14d / 30d), persisted in `localStorage`.

---

## 2026-06-23 — Slice 74: Shared ruling badges on Overview trends

### Slice 74: Color-coded ruling badges in trend table

- **`RulingBadge.tsx`** — shared kill/scale/pause/continue badge (extracted from Active Experiments).
- **Overview** — trend table uses `RulingBadge` instead of plain ruling text.

---

## 2026-06-23 — Slice 73: Stale snapshot hints on Overview trends

### Slice 73: Persist attention filter and flag stale snapshots

- **Desktop Overview** — persists “Attention only” in `localStorage`.
- Trend table marks snapshot dates older than the selected Overview date as stale.

---

## 2026-06-23 — Slice 72: Latest snapshot date in trend table

### Slice 72: Snapshot date column on Overview CAC trends

- **Desktop Overview** — trend table shows each experiment's `latest_snapshot_date` within the lookback window.

---

## 2026-06-23 — Slice 71: Attention-only trend toggle on Overview

### Slice 71: Filter CAC trends to flagged experiments

- **Desktop Overview** — “Attention only” checkbox wires `attention_only=true` on trend-summary fetch.
- Empty state when the filter returns no flagged experiments.

---

## 2026-06-23 — Slice 70: Trend attention highlighting

### Slice 70: Flag experiments needing attention in CAC trends

- **Trend summary** — `needs_attention` per experiment, `needs_attention_count`, sorted attention-first.
- **`GET /experiment/trend-summary?attention_only=true`** — filter to flagged experiments only.
- **Overview** — BEP column, red CAC when above break-even, row highlight + attention count.

---

## 2026-06-23 — Slice 69: Operator readiness banner on Overview

### Slice 69: Readiness status in the desktop Overview

- **`OperatorReadinessBanner.tsx`** — shows ready/not-ready, integration summary, blockers, and warnings.
- **Overview** — fetches `GET /operator/readiness` for the selected date and refreshes after run-cycle.

---

## 2026-06-23 — Slice 68: Trend summary as-of date

### Slice 68: Overview date scopes CAC trends

- **`GET /experiment/trend-summary?as_of=`** — end lookback on a specific date (default today).
- **Desktop Overview** — passes selected date to trend summary; refreshes report and trends after run-cycle.

---

## 2026-06-23 — Slice 67: Operator readiness API

### Slice 67: `GET /operator/readiness`

- **`GET /operator/readiness`** — unified readiness over HTTP; optional `date` and `strict`.
- **`evaluate_operator_readiness()`** — accepts `snapshot_date` for scoped snapshot gaps.
- **Deploy verifier** — also checks `/operator/readiness` after health-panel.
- **Desktop client** — `fetchOperatorReadiness()`.

---

## 2026-06-23 — Slice 66: Experiment trend summary on Overview

### Slice 66: Active experiment CAC trends

- **`marketmind/experiment_trend_summary.py`** — CAC direction per active experiment over a lookback window.
- **`GET /experiment/trend-summary`** — optional `days` query param (default 14).
- **Desktop Overview** — table of active experiments with latest CAC, trend arrow, and ruling.

---

## 2026-06-23 — Slice 65: CI deploy verification job

### Slice 65: Run verify script against live API in CI

- **`marketmind/deploy_verify.py`** — testable `verify_marketmind_deploy()` extracted from the script.
- **CI `deploy-verify` job** — starts uvicorn, polls `/health`, runs `verify_marketmind_deploy.py`.
- **`scripts/verify_marketmind_deploy.py`** — thin CLI wrapper over the shared module.

---

## 2026-06-23 — Slice 64: Health panel snapshot date

### Slice 64: Overview date drives snapshot-gap checks

- **`GET /operator/health-panel?date=`** — optional ISO date scopes `snapshot_gaps` (default today).
- **Desktop Overview** — passes the selected date into `fetchOperatorHealthPanel(date)` so
  the snapshot banner matches the report date picker.

---

## 2026-06-23 — Slice 63: Unified operator readiness check

### Slice 63: One local script for Gmail + commerce + preflight

- **`marketmind/operator_readiness.py`** — `evaluate_operator_readiness()` merges
  masked Gmail/commerce env status with local preflight and health warnings.
- **`scripts/check_operator_readiness.py`** — operator CLI; `--json` and `--strict`
  (fail on warnings, not only preflight blockers).

---

## 2026-06-23 — Slice 62: Snapshot gap detection

### Slice 62: Active experiments missing today's snapshot

- **`marketmind/snapshot_gaps.py`** — lists active experiments with no snapshot for a date.
- **`GET /operator/snapshot-gaps`** — optional `date` query param (default today).
- **Health panel** — snapshot status banner + warning when gaps exist.
- **`operator_health`** — includes `snapshot_gaps` in consolidated payload.

---

## 2026-06-23 — Slice 61: Operator run-cycle API + desktop trigger

### Slice 61: Manual daily cycle from API/desktop

- **`POST /operator/run-cycle`** — runs `run_daily_cycle` (safe; no external spend).
  Optional `date` query param (ISO, defaults to today).
- **Desktop Overview** — “Run cycle now” button on the health panel; refreshes
  pending approvals and last-cycle status after completion.
- **`runOperatorDailyCycle()`** in `desktop/src/api/client.ts`.

---

## 2026-06-23 — Slice 60: Daily cycle ledger status

### Slice 60: Last daily cycle in operator health

- **`marketmind/cycle_status.py`** — records `runner.daily_cycle` events to the operator
  ledger after each `run_daily_cycle` (CLI, scheduler, or API-triggered later).
- **`GET /operator/last-cycle`** — returns the most recent cycle summary.
- **Health panel** — shows last cycle date, experiments evaluated, approvals queued.
- **`runner.py`** — appends ledger entry on every completed cycle.

---

## 2026-06-23 — Slice 59: Stripe/Shopify integration readiness

### Slice 59: Commerce credential status in health panel

- **`marketmind/commerce_integrations.py`** — read-only Stripe/Shopify env presence checks.
- **`integrations_status`** — exposes `stripe` and `shopify` blocks with `live_ready` flags.
- **`operator_health`** — warns when `MARKETMIND_ENABLE_LIVE_WRITES=true` but commerce APIs
  are not live-ready.
- **Desktop health panel** — Gmail / Stripe / Shopify integration row.
- **`scripts/check_commerce_config.py`** — masked operator readiness check.

---

## 2026-06-23 — Slice 58: Operator health panel + deploy verification

### Slice 58: Consolidated operator health

- **`marketmind/operator_health.py`** — aggregates preflight, integrations, portfolio,
  ad spend, and checklist config in one read-only payload.
- **`GET /operator/health-panel`** — single endpoint for the desktop health panel.
- **`marketmind/experiment_portfolio.py`** — shared portfolio builder (DRY with `/experiment/portfolio`).
- **Desktop `OperatorHealthPanel.tsx`** — reusable panel; Overview uses one health fetch.
- **`scripts/verify_marketmind_deploy.py`** — post-deploy checks `/health` + `/operator/health-panel`.
- **`deploy_marketmind.ps1`** — runs verification after health poll.

---

## 2026-06-23 — Slice 57: Live Gmail API drafts

### Slice 57: Gmail `users.drafts.create` behind approval gates

- **`marketmind/adapters/gmail_client.py`** — `GmailClient` with OAuth refresh +
  live draft creation via Gmail REST API (httpx; no google SDK).
- **`gmail_config`** — `GMAIL_CLIENT_SECRET`, `live_ready`, `live_missing_secret` mode.
- Live path requires `MARKETMIND_GMAIL_DRY_RUN=false`, `MARKETMIND_ENABLE_LIVE_WRITES=true`,
  and full OAuth credentials.
- **`scripts/check_gmail_config.py`** — masked readiness check for operators.
- **`GET /operator/integrations`** — exposes `gmail.live_ready`.

---

## 2026-06-23 — Slice 56: Gmail integration gate (simulated live path)

### Slice 56: Gmail config + simulated draft on approved execute

- **`marketmind/gmail_config.py`** — `MARKETMIND_GMAIL_ENABLED`, `MARKETMIND_GMAIL_DRY_RUN`
  (default true), credential checks, `live_writes_allowed()`.
- **`marketmind/adapters/gmail_client.py`** — simulated Gmail draft creation when wired;
  live API explicitly blocked until a future slice.
- **`executor`** — `contact_supplier` with `dry_run=False` uses Gmail simulate path when
  enabled + creds; otherwise file-export dry-run or clear error.
- **`integrations_status`** — exposes `gmail.dry_run` and `live_writes.enabled`.
- **Desktop Overview** — shows Gmail mode and scheduler prune status.
- **`tests/test_gmail_config.py`**, extended executor/integration tests.

---

## 2026-06-23 — Slice 55: Overview ad spend + integration status

### Slice 55: Operator integration readiness

- **`marketmind/integrations_status.py`** — read-only Gmail/ad-import/scheduler flags.
- **`GET /operator/integrations`** — exposes `gmail.mode` (`draft_file_only` by default),
  latest ad CSV batch id, and scheduler prune env flags.
- **Desktop `Overview.tsx`** — imported ad spend cards alongside portfolio metrics.
- **`docker-compose.yml`** — scheduler passes `MARKETMIND_SNAPSHOT_PRUNE_APPLY` and retention days.
- **`.env.example`** — `MARKETMIND_GMAIL_ENABLED` documented (off by default).
- **`tests/test_integrations_status.py`**.

---

## 2026-06-23 — Slices 51–54: Gmail draft export, portfolio widget, scheduler, ad CSV

### Slice 51: Gmail-ready outreach draft export

- **`marketmind/gmail_draft.py`** — writes plain-text draft files to
  `logs/outreach_drafts/{approval_id}.txt` (no Gmail API; manual send).
- **`executor`** — `contact_supplier` dry-run saves draft file and returns `draft_file` path.
- **`GET /pipeline/outreach-draft/{approval_id}`** — returns stored outreach payload.
- **`tests/test_gmail_draft.py`** — file export tests.

### Slice 52: Portfolio summary on Overview

- **Desktop `Overview.tsx`** — experiment portfolio cards (counts, attention, lessons).
- **`fetchExperimentPortfolio()`** in `desktop/src/api/client.ts`.

### Slice 53: Docker scheduler service

- **`docker-compose.yml`** — `scheduler` service runs `marketmind-scheduler --hour 6`
  after API healthcheck; shares DB + logs volumes.
- **`docs/DEPLOYMENT.md`** — scheduler section updated.

### Slice 54: Ad CSV import + spend summary

- **`marketmind/ad_summary.py`** — aggregates latest ad import batch.
- **`POST /imports/ads/csv`**, **`GET /imports/ads/summary`**.
- **Desktop `LiveData.tsx`** — paste-to-import ad CSV + spend summary cards.
- **`tests/test_ad_summary.py`**, extended **`tests/test_api.py`**.

Suite: see `docs/qa/final_audit.md`.

---

## 2026-06-23 — Slices 43–48: Retention, validation, orders, outreach, lessons

### Slice 43: Snapshot retention

- **`marketmind/snapshot_retention.py`** — prune rows older than
  `MARKETMIND_SNAPSHOT_RETENTION_DAYS` (default 365).
- **`POST /snapshots/prune`** — dry-run by default.
- **`scripts/prune_snapshots.py`** — CLI operator tool.

### Slice 44: Experiment ID validation

- **`marketmind/experiment_ids.py`** — `exp_<slug>` format enforced on snapshot submit.
- Documented in **`AGENTS.md`**.

### Slice 45: Order lifecycle view

- **`marketmind/order_lifecycle.py`** — pipeline stages from import batches.
- **`GET /orders/lifecycle`** — read-only order list with stage counts.
- **Desktop:** order table on Live Data page.

### Slice 46: Supplier outreach drafts

- **`marketmind/outreach_drafts.py`** — dry-run email draft generator.
- **`POST /pipeline/prepare-supplier-outreach`** — queues `contact_supplier` approval.
- **`executor`** — `contact_supplier` dry-run handler.
- **Desktop:** Supplier Outreach page.

### Slice 47: Decision gate + commerce policy wiring

- **`marketmind/decision_gate.py`** — formal sequential gate runner.
- **`approvals.py`** — uses `DecisionGate`.
- **`executor.py`** — checks `commerce_approval_policy` before execution.
- **`commerce_approval_policy.py`** — action name aliases for approval-queue actions.

### Slice 48: Lessons library + report integration

- Daily report includes recent mistake lessons.
- **Desktop:** Lessons Library page (`GET /operator/mistakes`).
- **`desktop/src/api/client.ts`** — deduplicated; added order lifecycle, prune, outreach APIs.

Suite: see `docs/qa/final_audit.md`.

### Slice 49: Runner prune hook + lessons in cycle

- **`runner.py`** — daily report includes recent mistakes; optional
  `MARKETMIND_SNAPSHOT_PRUNE_ON_CYCLE` preview/apply via `snapshot_prune` in `RunResult`.

### Slice 50: Experiment portfolio summary

- **`GET /experiment/portfolio`** — counts by status, ruling, lessons recorded.

---

## 2026-06-23 — Slices 40–42: Checklist config, mistake tracker, deploy hardening

### Slice 40: Configurable checklist thresholds

- **`marketmind/checklist_config.py`** — reads `MARKETMIND_CHECKLIST_MIN_VISITS`,
  `MIN_ORDERS`, `MIN_SPEND` from env (defaults 100 / 5 / 50.0).
- **`marketmind/experiment_checklist.py`** — uses config instead of hardcoded values.
- **`GET /operator/checklist-config`** — exposes active thresholds.
- **`.env.example`**, **`docker-compose.yml`** — env passthrough.
- **`tests/test_checklist_config.py`** — 3 tests.

### Slice 41: Mistake tracker

- **`marketmind/mistake_tracker.py`** — append-only `logs/mistakes.jsonl` (Parts &
  Pieces `mistake_tracker` pattern). Categories: `cac_too_high`, `low_conversion`,
  `high_refunds`, `offer_miss`, `shipping_overrun`, `other`.
- **`GET /operator/mistakes`**, **`POST /operator/mistakes`** — list/record lessons.
- **`GET /experiment/{id}/mistakes`** — recorded + auto-suggested lessons from
  rulings, risks, and notes.
- **Desktop:** `MistakesSection` in Active Experiments; client helpers +
  Vitest coverage.
- **`tests/test_mistake_tracker.py`**, extended **`tests/test_operator.py`**.

### Slice 42: Deployment hardening

- **`scripts/deploy_marketmind.ps1`** — build, start, health-poll.
- **`scripts/rollback_marketmind.ps1`** — stop + rollback checklist.
- **`docker-compose.yml`** — healthcheck, logs volume, checklist env.
- **`docs/DEPLOYMENT.md`** — post-deploy verification, backup, rollback.
- **`docs/issues/0002-deploy-rollback-runbook.md`** — dated issue record.
- **`tests/test_api.py::test_execute_defaults_to_dry_run`** — API safety regression.

Suite: **374** Python passing; ruff clean.

---

## 2026-06-23 — Slice 39: Operator Health Panel (desktop)

Wires the Parts & Pieces backend endpoints (`/operator/preflight`,
`/experiment/{id}/checklist`) into the desktop dashboard so Aidan can see
system readiness and scale-readiness without calling the API manually.

### Desktop API client

- **`desktop/src/api/client.ts`**
  - `OperatorPreflight`, `ExperimentAttention`, `ChecklistItem`,
    `ExperimentChecklist` interfaces.
  - `fetchOperatorPreflight()` → `GET /operator/preflight`.
  - `fetchExperimentChecklist(id)` → `GET /experiment/{id}/checklist`.

### Desktop UI

- **`desktop/src/components/Overview.tsx`**
  - Preflight banner at top: `safe_to_operate` status, blockers list, experiments
    needing attention (kill / pause_ads rulings).
- **`desktop/src/components/ActiveExperiments.tsx`**
  - `ChecklistSection` in expanded active experiment cards: scale-readiness items
    with pass/fail, evidence, and blocker summary.
- **`desktop/src/index.css`**
  - `.alert-ok` style for the green preflight-safe banner.

### Tests added

- **`desktop/src/api/client.test.ts`** — 2 tests: preflight GET URL/shape;
  checklist GET URL/shape.

Suite: **360** Python + **9** Vitest passing; ruff clean.

---

## 2026-06-23 — Parts & Pieces Integration

All applicable patterns from the `Parts-and-Pieces` shared library have been
adopted and wired into MarketMind. See `docs/adr/2026-06-23-parts-reuse.md`
for the full decision record.

### Docs added

- **`AGENTS.md`** — Binding AI agent and developer instructions: reading order,
  prime directive, HIGH_RISK_ACTIONS table, definition of done, Parts-and-Pieces origin map.
- **`OWNER_MANUAL.md`** — Full operator manual: daily flow, common tasks, what not to do,
  dev setup, env vars, run/rollback commands, health checks, decision log, risks, parts used,
  handoff checklist.
- **`OPERATING_INDEX.md`** — Navigation front door: reading order, system map, daily flow,
  key invariants, Parts-and-Pieces integration table.
- **`docs/adr/2026-06-23-parts-reuse.md`** — ADR recording every Parts-and-Pieces module
  evaluated, the adopt/defer/skip decision for each, and the integration plan.

### Python utilities placed and wired

- **`marketmind/event_ledger.py`** — Append-only JSONL operator audit log
  (from `parts/python/event_ledger`). Writes to `logs/operator_events.jsonl`.
  Exposed via `POST /operator/log-event`.
- **`marketmind/commerce_approval_policy.py`** — MarketMind-specific approval policy
  (from `parts/python/approval_policy`). Defines `HIGH_RISK_ACTIONS`,
  `BLOCKED_ACTIONS`, and `AUTO_ALLOWED_ACTIONS` for commerce operations.
- **`marketmind/experiment_checklist.py`** — Scale-readiness checklist gate
  (from `parts/python/checklist_gate`). 8 conditions: active status, min 100 visits,
  5 orders, CAC ≤ break-even, zero consecutive losses, snapshot exists, ≥$50 spend.
  Exposed via `GET /experiment/{id}/checklist`.
- **`marketmind/operator_preflight.py`** — Operator preflight check
  (from `parts/python/operator_status`). Reports pending approvals, experiments with
  kill/pause_ads rulings, and a `safe_to_operate` flag.
  Exposed via `GET /operator/preflight`.

### New API router

- **`marketmind/api/routers/operator.py`** registered at `/operator`:
  - `GET /operator/preflight` — system readiness (pending approvals, attention flags)
  - `POST /operator/log-event` — append event to operator audit log

### Experiments router extended

- `GET /experiment/{id}/checklist` — scale-readiness checklist for one experiment;
  404 for unknown; each item has `item_id`, `description`, `required`, `passed`, `evidence`.

### Tests added

- **`tests/test_operator.py`** — 10 tests: preflight safe when empty, includes pending
  approvals, flags kill ruling; log-event returns logged, rejects blank type/id;
  checklist 404, not ready with zeros, ready with good snapshot, response shape.
- **`tests/test_commerce_approval_policy.py`** — 7 unit tests: blocked action, auto-allowed,
  high-risk without/with approval, empty action, risk flags surfaced, unknown action.
- **`tests/test_experiment_checklist.py`** — 9 unit tests: ready with good data, not ready
  inactive/few visits/few orders/cac over bep/consecutive losses/no snapshot/low spend,
  item field shape.

Suite: **360 passing**; ruff clean.

---

## 2026-06-16 — Slice 38: Experiment Notes

### Added

**`marketmind/db/models.py`**
- `ExperimentNoteRow` — `id`, `experiment_id`, `created_at`, `body`; auto-created
  via `Base.metadata.create_all` (`:memory:` tests) and picked up by alembic for
  file DBs.

**`marketmind/api/routers/experiments.py`**
- `POST /experiment/{id}/notes` — appends an operator note; 404 for unknown
  experiments, 422 for blank body.
- `GET /experiment/{id}/notes` — returns all notes oldest-first; empty list for
  unknown experiments.

**`desktop/src/api/client.ts`**
- `ExperimentNote` interface, `addExperimentNote(id, body)`,
  `getExperimentNotes(id)`.

**`desktop/src/components/ActiveExperiments.tsx`**
- `NotesSection` sub-component in expanded card: loads existing notes on open,
  inline textarea + Add button to append. Notes shown oldest-first with date prefix.

**`tests/test_experiment_notes.py`**
- 7 tests: add returns note; GET empty before add; GET all in order; 404 for unknown;
  422 for blank body; GET empty for unknown; isolation between experiments.

Suite: **334 passing**; ruff clean.

---

## 2026-06-16 — Slice 37: Experiment Status Management

### Added

**`marketmind/api/routers/experiments.py`**
- `PATCH /experiment/{id}/status` — accepts `{status: "active"|"ended"}`. Setting
  `ended` stamps `ended_at` with today's ISO date; setting `active` clears it.
  Returns 404 for unknown experiments, 422 for invalid status values.

**`desktop/src/api/client.ts`**
- `patchExperimentStatus(experimentId, status)` wired to `PATCH /experiment/{id}/status`.

**`desktop/src/components/ActiveExperiments.tsx`**
- "End experiment" / "Reactivate" button in expanded card body. Fires
  `patchExperimentStatus` then reloads the list. Shows inline error on failure.

**`tests/test_experiment_status.py`**
- 6 tests: end sets `ended_at`; reactivate clears it; 404 for unknown; 422 for invalid
  status; status reflected in `/experiment/active` list; `ended_at` cleared on reactivate.

Suite: **327 passing**; ruff clean.

---

## 2026-06-16 — Slice 36: Active Experiments Dashboard

### Added

**`marketmind/api/routers/experiments.py`**
- `GET /experiment/active` — returns all experiments from the DB, each with the
  latest snapshot's ruling (from the rule engine), actual CAC, risk list, and latest
  snapshot date. Experiments with no snapshots return `ruling: null`. The latest
  snapshot is determined by `snapshot_date DESC` per experiment.

**`desktop/src/api/client.ts`**
- `ActiveExperiment` interface and `listActiveExperiments()` function wired to
  `GET /experiment/active`.

**`desktop/src/components/ActiveExperiments.tsx`**
- Expandable card list of all experiments — collapse shows ID, status badge, ruling
  badge (colour-coded), and current CAC.
- Expanded card shows break-even CAC, latest snapshot date, start/end dates, and risk list.
- Filter bar: all / active / ended.
- Warning banner when any experiment needs attention (kill / pause / scale).

**`desktop/src/App.tsx`**
- New "Active Experiments" nav entry (13th page) wired to `<ActiveExperiments />`.

**`tests/test_active_experiments.py`**
- 7 tests: empty list, no-snapshot experiment, ruling computed from latest snapshot,
  most-recent-snapshot selection, multiple experiments returned, response shape,
  ruling value membership.

---

## 2026-06-16 — Slice 35: Experiment Trend View

### Added

**`marketmind/api/routers/snapshots.py`**
- `GET /snapshots/trend/{experiment_id}?days=N` — returns all snapshots for one
  experiment across all dates within the last N days (default 30), sorted by date
  ascending. Returns `[]` for unknown experiments. Each row includes computed fields
  (`actual_cac`, `conversion_rate`, `add_to_cart_rate`, `refund_rate`, `break_even_cac`).

**`desktop/src/components/SnapshotTrend.tsx`**
- Experiment ID input + days selector + Load button.
- SVG line chart: actual CAC line (solid), break-even CAC reference (dashed amber),
  avg order value (dashed green). X-axis labels are MM-DD dates.
- Summary row: total orders, revenue, spend, avg CAC (green/red vs break-even).
- Daily breakdown table (date, orders, revenue, ad spend, CAC, conv%, refund%).

**`desktop/src/api/client.ts`**
- `getSnapshotTrend(experimentId, days?)` function.

**`desktop/src/App.tsx`**
- Added `"trend"` page type, nav entry with waveform icon, renders `<SnapshotTrend />`.

**`tests/test_snapshot_trend.py`** (7 tests)
- Empty for unknown experiment; date ordering; computed fields present; `days` filter;
  default 30-day window; multi-experiment isolation; date in response.

Suite: **314 passing**; ruff clean.

---

## 2026-06-16 — Slices 33 + 34: Import History dashboard & Snapshot Recording API

### Added

**`marketmind/api/routers/snapshots.py`** (Slice 34)
- `POST /snapshots` — records an `ExperimentSnapshot` into the DB for a given
  date; defaults to today. Returns `{recorded, experiment_id, snapshot_date}`.
- `GET /snapshots?snapshot_date=` — lists all snapshots for a date, hydrated
  with computed fields: `conversion_rate`, `actual_cac`, `add_to_cart_rate`,
  `refund_rate`.
- `GET /snapshots/{experiment_id}?snapshot_date=` — filtered by experiment;
  404 when date is explicit and nothing is found.

**`desktop/src/components/ImportHistory.tsx`** (Slice 33)
- Source filter dropdown + refresh; table of all import batches (id, source
  label, timestamp, counts). Click row → full row detail panel.

**`desktop/src/components/SnapshotRecorder.tsx`** (Slice 34)
- Two-column layout: left is a form (experiment ID, product name, break-even
  CAC, date, and all performance counters); right is the live snapshot table
  for the chosen date. Submitting re-loads the table. CAC column coloured
  green/red relative to break-even.

**`desktop/src/api/client.ts`** (Slices 33 + 34)
- `ImportBatch`, `ImportBatchDetail` types; `pullAndSave*`, `listImportHistory`,
  `getImportBatch` functions.
- `SnapshotRequest`, `SnapshotRecord` types; `submitSnapshot`, `listSnapshots`
  functions.

**`desktop/src/App.tsx`** (Slices 33 + 34)
- Added `"history"` and `"snapshots"` page types; nav entries with icons;
  renders `<ImportHistory />` and `<SnapshotRecorder />`.

**`tests/test_snapshots.py`** (9 tests)
- POST records and returns correct date; GET empty before submit; GET populated
  after submit; conversion rate + CAC computed correctly; experiment filter;
  404 on miss; default-date behaviour; multi-experiment list.

### Changed

**`marketmind/api/app.py`**
- Registered `snapshots` and `webhooks` routers.

Suite: **302 passing**; ruff clean.

---

## 2026-06-16 — Slice 32: Webhook ingestion (Stripe + Shopify)

### Added

**`marketmind/webhooks.py`**
- `verify_stripe_signature(payload, sig_header, secret)` — Stripe HMAC-SHA256 with
  5-minute replay protection; raises `ValueError` on mismatch or stale timestamp.
- `normalize_stripe_event(event)` — maps `charge.*` event to `ImportResult`.
- `verify_shopify_signature(payload, hmac_header, secret)` — Base64-encoded
  HMAC-SHA256 per Shopify's webhook spec.
- `normalize_shopify_order_event(payload)` — maps order webhook payload to `ImportResult`.

**`marketmind/api/routers/webhooks.py`** — 2 new endpoints
- `POST /webhooks/stripe` — verifies `stripe-signature`, normalizes event, persists
  batch; 409 if `STRIPE_WEBHOOK_SECRET` unset, 400 if signature invalid.
- `POST /webhooks/shopify/orders` — verifies `x-shopify-hmac-sha256`, normalizes
  order event, persists batch; 409 if `SHOPIFY_WEBHOOK_SECRET` unset.

**`tests/test_webhooks.py`** (9 unit tests)
- Stripe: valid sig, bad sig, replayed timestamp, missing header fields.
- Stripe normalization: event_type, object_id, amount.
- Shopify: valid sig, bad sig.
- Shopify normalization: paid order, refunded order.

**6 API tests added to `tests/test_api.py`**
- 409 without secret, 400 without header, 400 bad sig, 200 valid Stripe webhook
  with batch_id in response.

Suite: **298 passing**; ruff clean.

---

## 2026-06-16 — Slice 31: Nightly run scheduler

### Added

**`marketmind/scheduler.py`**
- `run_scheduler(hour, run_now, once)` — blocks and fires `run_daily_cycle` each
  day at the configured local hour. `--once` mode exits after one cycle (for cron).
  Exceptions in a cycle are caught and logged; the loop never crashes permanently.
- `main()` — argparse CLI: `--hour N`, `--now` (fire immediately then schedule),
  `--once`.
- `_seconds_until(hour, minute)` — pure helper: seconds until the next occurrence
  of a local wall-clock time (wraps to tomorrow if already passed today).

**`marketmind-scheduler` CLI entrypoint** (`pyproject.toml`)
- `marketmind-scheduler` installed alongside `marketmind` for direct invocation
  by systemd or Docker `CMD`.

**`docs/marketmind-scheduler.service`**
- Drop-in systemd unit file for bare-metal / VPS deployments. Points at
  `/opt/marketmind/.venv/bin/marketmind-scheduler --hour 6`; `Restart=on-failure`.

**`marketmind/cli.py`**
- Added `scheduler` command: `marketmind scheduler` proxies to `scheduler.main()`.

**`tests/test_scheduler.py`** (7 tests)
- `_seconds_until` future/past/exact-minute coverage.
- `run_scheduler --once` fires one cycle and returns.
- CLI arg parsing: `--once`, `--hour`, `--now`.

Suite: **284 passing**; ruff clean.

---

## 2026-06-16 — Slice 30: Alembic migrations

### Added

**`alembic/versions/0002_add_import_batches.py`**
- Migration that adds the `import_batches` table with all columns (Slice 29 schema).
- Reversible: `downgrade()` drops the table.

**`alembic.ini`**
- Added `path_separator = os` to silence the Alembic deprecation warning.

**`tests/test_migrations.py`** (7 tests)
- `test_upgrade_head_creates_all_tables` — all 5 app tables + `alembic_version` present.
- `test_upgrade_is_idempotent` — running head twice does not error.
- `test_downgrade_0001_removes_import_batches` — selective downgrade works.
- `test_downgrade_base_drops_all` — full rollback leaves no app tables.
- `test_round_trip_upgrade_downgrade_upgrade` — full up → down → up succeeds.
- `test_import_batches_columns` — column set matches the ORM model.
- `test_current_version_is_head` — `alembic_version` records `0002` after upgrade.

### Changed

**`marketmind/api/app.py` lifespan**
- Real file DBs now call `alembic upgrade head` on startup instead of bare
  `create_all`, so schema evolves automatically with each release.
- In-memory SQLite (tests and injection) still uses `create_all` since Alembic's
  version table cannot persist in `:memory:`.

Suite: **277 passing**; ruff clean.

---

## 2026-06-16 — Slice 29: Import history persistence

### Added

**`marketmind/db/models.py` — `ImportBatchRow` table**
- New `import_batches` table: `source`, `pulled_at`, `total_rows`, `ok_count`,
  `review_count`, `rows_json` (JSON TEXT). Schema created on startup via `create_all`.

**`marketmind/db/import_store.py`**
- `save_import(engine, result) -> int` — persist an `ImportResult`; returns batch id.
- `list_imports(engine, source?, limit) -> list[dict]` — recent batches, newest first,
  summary fields only (no row data, safe to list at scale).
- `get_import(engine, batch_id) -> dict | None` — full batch including all row dicts.

**`marketmind/api/routers/imports.py` — 5 new endpoints**
- `POST /imports/pull/stripe/orders` — pull + persist + return summary + batch_id.
- `POST /imports/pull/shopify/orders` — same for Shopify orders.
- `POST /imports/pull/shopify/products` — same for Shopify products.
- `GET /imports` — list history (optional `source=` filter).
- `GET /imports/{batch_id}` — full batch detail with rows.

**Dashboard: `LiveData.tsx` updated**
- Pull button now calls the persisting `/imports/pull/*` endpoints.
- Pull history panel shows past batches for the active source tab (auto-refreshes
  after each pull via `listImportHistory`).

8 unit tests in `tests/test_import_store.py`; 5 API tests added to `tests/test_api.py`.
Suite: **270 passing**; ruff clean.

---

## 2026-06-16 — Slice 28: Live Data dashboard page

### Added

**`desktop/src/components/LiveData.tsx`**
- New **Live Data** page (9th sidebar item) that surfaces the three `/sources/*`
  endpoints added in Slice 27 directly in the dashboard.
- Source picker tabs: Stripe Charges / Shopify Orders / Shopify Products.
- Pull-on-demand button — no background polling. Results rendered in a responsive
  scrollable table with total/OK/review row counts.
- 409 (missing credentials) is caught and surfaced as a plain-English message
  rather than a raw error.
- No credentials are ever stored in the frontend; the page only calls the API.

**`desktop/src/api/client.ts`**
- Added `ImportRow`, `ImportResult` types and `fetchStripeOrders`,
  `fetchShopifyOrders`, `fetchShopifyProducts` functions.

**`desktop/src/index.css`**
- Added `.dim`, `.btn-secondary`, `.error-banner`, and `.data-table` CSS classes
  used by the new page.

Build: 257 backend tests pass; 8 frontend Vitest tests pass; TypeScript + ruff clean.

---

All notable changes to MarketMind Autopilot are recorded here.
Format: each entry has a date, a type (Added / Changed / Fixed / Removed), and a short description.
This file is part of the Parts & Pieces starter package requirement.

---

## 2026-06-16 — Slice 26: packaging (Docker + deployment docs)

### Added

**Backend container (`Dockerfile`, `.dockerignore`, `docker-compose.yml`)**
- `python:3.12-slim` image; `pip install .`; serves uvicorn on `:8000`.
- SQLite persists on a `/data` volume; schema created on startup.
- `MARKETMIND_API_TOKEN` enables bearer-token auth at runtime; live integration
  secrets passed at runtime only (never baked into the image).
- `.dockerignore` keeps the build context free of `desktop/`, tests, secrets,
  and local artifacts.

**`docs/DEPLOYMENT.md`**
- How to build/run the backend (Docker + compose) and the desktop Tauri
  installer (`npm run tauri build` → NSIS `.exe` / MSI under
  `src-tauri/target/release/bundle/`), pointing the app at a remote API, and a
  release checklist.

---

## 2026-06-16 — Slice 25: frontend test harness (Vitest)

### Added

**Vitest + Testing Library (`desktop/`)**
- `vitest.config.ts` (jsdom env), `src/test/setup.ts` (jest-dom matchers),
  `npm test` script. Test files are excluded from the strict `tsc` build so
  `npm run build` stays clean; Vitest type-checks/runs them separately.
- `src/api/client.test.ts` (5): GET URL, POST JSON body, Authorization header
  present/absent by stored token, error → `status: detail` throw.
- `src/components/ScoreResultView.test.tsx` (3): verdict/name/reason render,
  criterion rows + risks, channel chip.
- CI `frontend` job now runs `npm test` after the build. The React app went
  from zero tests to a working harness + 8 tests.

---

## 2026-06-16 — Slice 24: optional API bearer-token auth

### Added

**`marketmind/api/auth.py` — bearer-token middleware**
- If `MARKETMIND_API_TOKEN` is set, every request must carry
  `Authorization: Bearer <token>` (constant-time compared); 401 otherwise.
- If unset, the API stays open (local-dev default) and logs a one-time warning
  so an unauthenticated deployment is never silent.
- Allowlist (`/health`, `/docs`, `/redoc`, `/openapi.json`) is always reachable.
- This is the floor that lets the backend leave localhost safely.

**Client + docs**
- `desktop/src/api/client.ts` sends the token from `localStorage`
  (`marketmind_api_token`) when present; unset by default.
- `.env.example` documents `MARKETMIND_API_TOKEN`.
- 3 tests in `tests/test_auth.py` (open when unset; 401/200 when set; health
  always open). Suite now **247 passing**.

---

## 2026-06-16 — Slice 22-23: executor API + dashboard execute/prepare

### Added

**Executor API (`marketmind/api/routers/execution.py`)**
- `POST /execute/{approval_id}` — execute one APPROVED action (dry_run default
  True). 404 if missing, 409 if refused (not approved / no payload / no creds).
- `POST /execute` — batch-execute all un-executed APPROVED actions.
- `GET /execute/log` — the append-only execution log.
- 3 API tests incl. full prepare→approve→execute over HTTP.

**Desktop dashboard wiring (`desktop/`)**
- Approval Queue: an **Execute (dry-run)** button on APPROVED records, showing
  the executor result inline.
- New **Prepare Offer** page: fills an offer + channel, calls
  `POST /pipeline/prepare-offer`, and shows the queued approval to take to the
  Approval Queue. Sidebar now has 8 pages.
- `client.ts`: `prepareOffer`, `executeApproved`, `fetchExecutionLog`.

Suite now **244 passing**; desktop frontend type-checks + builds.

---

## 2026-06-16 — Slice 21: offer → approval pipeline

### Added

**`marketmind/pipeline.py` — `prepare_offer_for_approval(engine, offer_context, channel)`**
- Closes the last gap between scoring an offer and executing an approved action:
  `OfferContext → generate_offer_spec → build channel payload → create gated
  approval (HIGH → PENDING) → record_action_payload`.
- Channels: `stripe` (→ `create_stripe_payment_link`) and `shopify`
  (→ `publish_shopify_product`). Unknown channels raise.
- No money / no external calls: payload built dry-run, approval lands PENDING.
  The operator approves; the executor then runs it (live still needs creds).

**API: `POST /pipeline/prepare-offer`**
- Accepts an offer context + channel, returns the resulting PENDING approval.

**Tests**
- `tests/test_pipeline.py` (6): unknown channel, stripe/shopify approval shape,
  end-to-end prepare→approve→execute for both channels, execute-before-approval
  refused.
- 2 API tests for the endpoint. Suite now **241 passing**.

---

## 2026-06-16 — Slice 20: adapter-backed execution (Stripe + Shopify)

### Added

**Executor handlers for adapter-backed actions (`marketmind/executor.py`)**
- `record_action_payload(engine, approval_id, payload)` — attaches an action's
  payload to an approval via the event ledger (`approval_payload` event), so no
  schema change to the approvals table is needed.
- `create_stripe_payment_link` handler: dry-run goes through the gate-enforced
  `simulate_create_payment_link` (no HTTP); live requires `STRIPE_API_KEY` in
  the environment and calls `StripeClient.create_payment_link`.
- `publish_shopify_product` handler: dry-run via `simulate_create_product_draft`;
  live requires `SHOPIFY_STORE_DOMAIN` + `SHOPIFY_ACCESS_TOKEN` and calls
  `ShopifyClient.create_product_draft`.
- Safety unchanged: APPROVED-only, dry-run default, live refused without creds
  (safe-fail), idempotent per approval_id, secrets never logged or returned.
- 6 more tests in `tests/test_executor.py` (dry-run simulate, missing-payload
  refusal, live-without-creds refusal, live with mocked client + secret-leak
  check). Suite now 233 passing.

---

## 2026-06-16 — Slice 19: approved-action executor + event ledger

### Added

**Event ledger writer (`marketmind/db/event_store.py`)**
- `append_event` / `list_events` / `event_exists` — the append-only writer for
  the `events` table, which had existed since Slice 11 with no writer. Payloads
  are JSON-serialized to TEXT; events are never updated or deleted.

**Slice 19: approved-action executor (`marketmind/executor.py`)**
- `execute_approved(engine, approval_id, dry_run=True)` — acts on an APPROVED
  request, the hand on the far side of the approval gate. Closes the loop:
  runner queues scale → human approves → executor applies it.
- `execute_all_approved(engine, dry_run=True)` — batch over all un-executed
  APPROVED records; per-action refusals are captured, never block the batch.
- `execution_log(engine)` — the append-only record of what was executed.
- Safety: refuses anything not APPROVED; `dry_run=True` default (records intent,
  no spend/external call); live execution of ad-budget scaling is refused
  (no integration wired — safe-fail, never a silent spend); idempotent per
  approval_id via the event ledger.
- 10 tests in `tests/test_executor.py`.

---

## 2026-06-16 — CI pipeline + Slice 18: experiment-runner loop

### Added

**Continuous integration (`.github/workflows/ci.yml`)**
- `backend` job: `ruff check .` + `pytest -q` on Python 3.12.
- `frontend` job: `npm ci` + `npm run build` (TypeScript type-check + Vite build)
  for the Tauri desktop app under `desktop/`.
- Runs on every push to `main` and every PR targeting `main`. Closes the gap
  where `main` had no automated test gate after the slice PRs were merged.

**Slice 18: experiment-runner loop (`marketmind/runner.py`)**
- `record_snapshot(engine, snapshot, date)` — persists an observed
  `ExperimentSnapshot`, upserting the `ExperimentRow` header.
- `hydrate_snapshots(engine, date)` — loads a day's snapshots back into domain
  objects (joins snapshot rows with their experiment headers).
- `run_daily_cycle(engine, date)` — the orchestrator the project was built
  toward: hydrate → `evaluate_experiment` per snapshot → queue SCALE requests
  for approval → `generate_daily_report`. Returns a structured `RunResult`.
- Safety: never spends money, never calls an external API. The only action it
  creates is a HIGH-risk `scale_campaign` request, which lands PENDING (never
  auto-approved). KILL/PAUSE/REVISE rulings need no approval. Scale-approval
  creation is idempotent per (experiment, date).
- `marketmind run-cycle` CLI command runs one cycle against the configured DB.
- 9 tests in `tests/test_runner.py` (round-trip persistence, each ruling type,
  idempotency, mixed-portfolio aggregation).

---

## 2026-06-15 — Slices 6–10: Approval queue, CSV import, daily report, Stripe + Shopify adapters

### Added

**Slice 6: Approval queue (`marketmind/approvals.py`)**
- `RiskLevel` / `ApprovalStatus` / `ApprovalRecord` schemas.
- `classify_action_risk(action) -> RiskLevel` — registry of 25 known actions
  (LOW/MEDIUM/HIGH/CRITICAL); unknown actions default to HIGH (safe-fail).
- `make_approval_record()` — convenience constructor with UUID-based IDs.
- `evaluate_approval(record) -> ApprovalRecord` — sequential gate adapted from
  P&P `DecisionGate`: CRITICAL→BLOCKED, HIGH→PENDING, MEDIUM→PENDING, LOW→AUTO_ALLOWED.
  HIGH records include checklist enforcement (P&P `ChecklistGate` pattern):
  rollback_plan, expected_cost, summary, and approval_id must all be present.
- 15 tests in `tests/test_approvals.py`.

**Slice 7: CSV import layer (`marketmind/importers.py`)**
- `ImportRowStatus` / `ImportRow` / `ImportResult` schemas.
- `import_products_csv()`, `import_ad_report_csv()`, `import_orders_csv()` —
  adapted from P&P `CsvSourceAdapter`. Accepts in-memory text; alias resolution
  for all three CSV shapes; bad rows go to `review_rows` with a note, never raise.
- 15 tests in `tests/test_importers.py`.

**Slice 8: Daily report generator (`marketmind/reports.py`)**
- `DailyMetrics` / `DailyReport` schemas.
- `generate_daily_report(date, snapshots, pending_approvals) -> DailyReport` —
  pure computation; adapted from P&P `JsonlEventLedger` replay pattern (caller
  hydrates snapshots from the ledger). Aggregates revenue/CAC/ROAS, surfaces
  risk signals from `rules.py` thresholds, derives lessons from ledger state.
- 14 tests in `tests/test_reports.py`.

**Slice 9: Stripe Payment Links adapter (`marketmind/adapters/stripe_adapter.py`)**
- `PaymentLinkPayload` schema.
- `build_payment_link_payload(offer_spec, approval, dry_run) -> PaymentLinkPayload` —
  dry-run only by default. Live creation requires HIGH+APPROVED `ApprovalRecord`
  AND explicit `dry_run=False`. No secrets logged, printed, or included in payload.
- 11 tests in `tests/test_stripe_adapter.py`.

**Slice 10: Shopify adapter (`marketmind/adapters/shopify_adapter.py`)**
- `ShopifyVariant` / `ProductDraftPayload` schemas.
- `build_product_draft(offer_spec, vendor, product_type, approval, dry_run)` —
  always `status="draft"`. Publishing requires HIGH+APPROVED `ApprovalRecord`
  AND explicit `dry_run=False`. No secrets in payload.
- 12 tests in `tests/test_shopify_adapter.py`.

### Parts & Pieces compliance
- Slice 6 uses `DecisionGate` + `ChecklistGate` patterns (inline adaptation, as
  mandated by ADR-0002).
- Slice 7 uses `CsvSourceAdapter` pattern (inline adaptation).
- Slices 8 adapts `JsonlEventLedger` replay pattern (pure-computation variant).

### Test count
132 tests total (was 62 before this session). All pass. Ruff clean.

---

## 2026-06-15 — Slice 5: Landing-page and offer spec generator

### Added
- `OfferContext` schema: operator-supplied inputs (product_name, sale_price,
  key_benefit, target_customer, secondary_benefits, common_objections,
  shipping_note, return_policy, niche).
- `FaqItem`, `BundleItem`, `AnalyticsEvent`, `OfferSpec` schemas.
- `marketmind/spec_generator.py`: `generate_offer_spec()` — deterministic,
  template-based. Produces headline, subheadline, bundle items, FAQ, CTA,
  6 standard analytics events, trust signals, Codex build notes, and 7
  `safety_flags` naming what Codex must NOT build (fake reviews, fake urgency,
  guaranteed results, hidden fees, etc.).
- `spec-sample` CLI command.
- 26 tests in `tests/test_spec_generator.py` covering all sections, safety
  flags, edge cases (no secondary benefits, no objections, no shipping/return
  note), and input validation.

### Parts & Pieces: `RunOnceChain` evaluated, not used
Spec sections are independent (all generated from the same fixed OfferContext,
not chained), so the sequential pipeline pattern adds indirection without benefit.
See ADR-0002.

---

## 2026-06-15 — Slice 4: Experiment rule engine

### Added
- `ExperimentSnapshot` schema: captures live test performance counters
  (visits, orders, ad spend, ATC, refunds, shipping). Derived properties
  (actual_cac, conversion_rate, add_to_cart_rate, refund_rate, shipping_overrun)
  computed from raw counters, never stored.
- `ExperimentRuling` + `ExperimentRulingResult` schemas.
- `marketmind/experiment_rules.py`: `evaluate_experiment()` applies PNL_MODEL
  kill/scale rules in strict priority — kill → pause → revise → scale → continue.
  Scale always sets `requires_approval=True`.
- Slice 4 kill/scale thresholds added to `rules.py`.
- 13 new tests in `tests/test_experiment_rules.py`.

### Fixed
- Duplicate `NICHE_SCORE_WEIGHTS` block in `rules.py` removed.

---

## 2026-06-15 — Slice 2: Scoring engine + Slice 1 hardening + Credential docs

### Added
- Slice 2 scoring engine (`marketmind/scoring.py`): `score_product`,
  `score_niche`, `classify_assumption`, `recommend_channel`.
  Explainable per-criterion breakdown; confidence capped by evidence quality.
  Unsourced claims can never be `VERIFIED`.
- Channel ladder: Stripe Payment Link → eBay/TikTok → Shopify → Amazon-later
  → do-not-sell.
- Scoring schemas: `ProductCandidate`, `NicheCandidate`, `AssumptionRecord`,
  `Channel`, `ChannelRecommendation`, `CriterionScore`, `ScoreResult`,
  `ScoreVerdict`, `AssumptionStatus`.
- Scoring weights/thresholds in `rules.py`.
- `score-sample` CLI command.
- 15 new tests in `tests/test_scoring.py`.
- `docs/API_KEYS_AND_CREDENTIALS.md`: sandbox-first, read-only-first,
  least-privilege credential setup guide (no real secrets).
- `ruff>=0.6` pinned in dev deps; `[tool.ruff]` config added to `pyproject.toml`.
- `*.egg-info/`, `build/`, `dist/` added to `.gitignore`.

### Fixed
- Rule-ordering bug: thin-margin + losing-after-ads product now correctly returns
  `REVISE_OFFER` (engine was right; the original test expectation was wrong).
- Long line in `math_engine.py` wrapped to satisfy E501.
- Test renamed to `test_thin_margin_losing_after_ads_revises_offer`.

### Changed
- `.env.example` upgraded to restricted-key model (Stripe restricted keys,
  `SHOPIFY_API_VERSION`, eBay sandbox OAuth, Amazon SP-API, ad-platform read-only).
- README: new credential doc linked.

---

## 2026-06-15 — Slice 1: Commerce math engine (initial build)

### Added
- Python package scaffold: `marketmind/`, `tests/`, `pyproject.toml`.
- `ProductCostInput` and `UnitEconomicsResult` schemas (`schemas.py`).
- `calculate_unit_economics()` engine (`math_engine.py`).
- Kill/scale business rules (`rules.py`).
- CLI dry-run sample (`cli.py`).
- 7 unit tests (`tests/test_math_engine.py`).
- `.env.example`, `.gitignore`, initial planning docs.
