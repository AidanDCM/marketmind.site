# Changelog

All notable changes to MarketMind Autopilot are recorded here.
Format: each entry has a date, a type (Added / Changed / Fixed / Removed), and a short description.
This file is part of the Parts & Pieces starter package requirement.

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
