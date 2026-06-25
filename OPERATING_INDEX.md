# MarketMind Autopilot — Operating Index

This is the front door. Read this first, then follow the links.

**If you are a new developer or AI agent:** read every file in the "Required reading order" section
before writing a single line of code.

**If you are Aidan running the system:** skip to section 3 (Normal daily flow).

---

## 1. Required reading order

1. [`README.md`](README.md) — what MarketMind is and why it exists
2. [`SLICE_WORKFLOW.md`](SLICE_WORKFLOW.md) — slice vs hardening phases, testing microscope
3. [`AGENTS.md`](AGENTS.md) — rules for AI agents and developers (binding)
4. [`OWNER_MANUAL.md`](OWNER_MANUAL.md) — how to install, run, test, deploy, and roll back
5. [`docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md`](docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md) — test commands and evidence
6. [`docs/engineering_log/README.md`](docs/engineering_log/README.md) — forensic change ledger
7. [`docs/issues/`](docs/issues/) — known failures and their fixes (read before touching related code)
8. [`CHANGELOG.md`](CHANGELOG.md) — slice summary
9. [`ARCHITECTURE.md`](ARCHITECTURE.md) — system layers, DB schema, API structure

---

## 2. System map

| Area | File | Purpose |
|---|---|---|
| Product North Star | [`README.md`](README.md) | Goal and safety stance |
| Agent/dev rules | [`AGENTS.md`](AGENTS.md) | What AI agents and devs must do |
| Operations manual | [`OWNER_MANUAL.md`](OWNER_MANUAL.md) | Run, test, deploy, rollback |
| Architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Layers, models, API map |
| Business model | [`PNL_MODEL.md`](PNL_MODEL.md) | Unit economics and margin model |
| Approval policy | [`APPROVAL_POLICY.md`](APPROVAL_POLICY.md) | What requires human approval |
| Codex handoff | [`CODEX_HANDOFF.md`](CODEX_HANDOFF.md) | Template for handing tasks to Codex |
| Development plan | [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) | Slice roadmap |
| Test plan | [`TEST_PLAN.md`](TEST_PLAN.md) | Test strategy |
| Slice workflow | [`SLICE_WORKFLOW.md`](SLICE_WORKFLOW.md) | Proceed = slice or hardening |
| Testing manual | [`docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md`](docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md) | Commands + evidence |
| Engineering log | [`docs/engineering_log/`](docs/engineering_log/) | Forensic per-change ledger |
| Audits | [`docs/audits/README.md`](docs/audits/README.md) | Audit triad standard |
| Local CI evidence | [`reports/local_ci/TEST_LOG.md`](reports/local_ci/TEST_LOG.md) | Append-only test runs |
| Deployment | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Deploy to VPS |
| Decisions | [`docs/decisions/`](docs/decisions/) | ADRs and major decisions |
| Issues | [`docs/issues/`](docs/issues/) | Known bugs and fixes |
| QA | [`docs/qa/`](docs/qa/) | QA reports and runbooks |

---

## 3. Normal daily flow (Aidan)

1. `uvicorn marketmind.api.app:app --reload` — start the backend
2. `cd desktop && npm run dev` — start the desktop app
3. **Overview** — check daily metrics, pending approvals, risks
4. **Approval Queue** — approve or deny any pending high-risk actions
5. **Active Experiments** — review kill/pause/scale rulings; add notes; end dead experiments
6. **Snapshots** — record today's performance for each active experiment
7. **Trend** — review any experiment running > 7 days
8. `GET /operator/preflight` — confirm `safe_to_operate: true` before any execution

---

## 4. Key invariants (never break these)

- The approval gate is the only path to real Stripe/Shopify writes. `dry_run=True` is
  the default for all execution endpoints. A human must approve before `dry_run=False`.
- `logs/operator_events.jsonl` is append-only. Never delete or edit entries.
- Experiment snapshots are the source of truth for P&L. Never edit them; add a correction
  snapshot instead.
- The rule engine (CONTINUE / PAUSE_ADS / REVISE_OFFER / KILL / SCALE_REQUIRES_APPROVAL)
  is read-only computation. It does not take actions — it only recommends.

---

## 5. Parts-and-Pieces integration

This repo uses patterns from `Parts-and-Pieces`. Adapted utilities live in `marketmind/`:

| MarketMind file | Source part | What it does |
|---|---|---|
| `marketmind/event_ledger.py` | `parts/python/event_ledger` | Append-only JSONL operator audit log |
| `marketmind/commerce_approval_policy.py` | `parts/python/approval_policy` | MarketMind-specific high-risk action list |
| `marketmind/experiment_checklist.py` | `parts/python/checklist_gate` | Scale-readiness checklist for experiments |
| `marketmind/operator_preflight.py` | `parts/python/operator_status` | Preflight: pending approvals + attention flags |
| `marketmind/mistake_tracker.py` | `parts/python/mistake_tracker` | Append-only experiment lessons |
| `marketmind/gmail_draft.py` | `parts/python/gmail_draft_client` | Plain-text outreach draft export (no live send) |
| `marketmind/ad_summary.py` | — | Ad spend totals from CSV import batches |

New API endpoints added by the integration:
- `GET /operator/preflight` — system readiness check
- `POST /operator/log-event` — append a named event to the operator audit log
- `GET /operator/checklist-config` — active scale-readiness thresholds
- `GET /operator/integrations` — Gmail/ad-import/scheduler readiness (read-only)
- `GET /operator/health-panel` — consolidated operator health; optional `date` for snapshot gaps
- `GET /operator/readiness` — unified Gmail/commerce/preflight readiness; optional `date`, `strict`
- `GET /operator/last-cycle` — most recent daily runner cycle from the operator ledger
- `POST /operator/run-cycle` — manually trigger one safe daily cycle (optional `date`)
- `GET /operator/snapshot-gaps` — active experiments missing a snapshot for a date
- `GET /operator/mistakes` / `POST /operator/mistakes` — experiment lesson tracker
- `GET /experiment/{id}/checklist` — scale-readiness checklist for one experiment
- `GET /experiment/{id}/mistakes` — recorded + suggested lessons for one experiment
- `GET /experiment/trend-summary` — CAC trends; optional `days`, `as_of`, `attention_only`
- `POST /imports/ads/csv` / `GET /imports/ads/summary` — ad CSV import and spend rollup
- `GET /pipeline/outreach-draft/{approval_id}` — supplier email draft payload

---

## 6. Current status

- **Active owner:** Aidan
- **Active maintainer:** Aidan / Codex agents
- **Current phase:** Hardening — Phase B pass 21 complete (docs drift r3); see `SLICE_WORKFLOW.md`
- **Last reviewed:** 2026-06-24
- **Test inventory:** ~728 pytest + 28 desktop Vitest files; `tests/test_docs_drift_contract.py` guards rotation 3 doc parity
- **Known blockers:** None

---

## Rule

If a new contributor cannot understand the system from this index and linked docs,
the docs are not good enough yet. File an issue and fix them.
