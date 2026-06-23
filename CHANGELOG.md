# Changelog

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
