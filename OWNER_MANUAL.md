# MarketMind Autopilot — Owner Manual

**Project:** MarketMind Autopilot  
**Repo:** `AidanDCM/marketmind.site`  
**Owner:** Aidan  
**Last updated:** 2026-06-23  
**Current status:** Building (active slice development)

---

## 1. What this project does

MarketMind Autopilot is a human-in-the-loop commerce operating system. It handles the
full loop from market research through kill/scale decisions — but never takes a high-risk
action without an explicit human approval.

```text
Research niche
  → Score product opportunity (scoring engine)
  → Estimate unit economics (break-even CAC, margins)
  → Generate offer spec (headline, bundle, FAQ, CTA)
  → Prepare Codex/developer handoff task
  → Human approval gate (Aidan approves or denies)
  → Build / launch
  → Record daily snapshots (visits, orders, ad spend, revenue)
  → Rule engine evaluates → CONTINUE / PAUSE / REVISE / KILL / SCALE
  → Log decision and lesson
  → Repeat
```

---

## 2. Normal operator use (Aidan's daily flow)

1. Open the desktop app (`npm run dev` in `desktop/`, backend running via `uvicorn`).
2. Check **Overview** — daily metrics, pending approvals, risks, recommendations.
3. Check **Approval Queue** — approve or deny any pending actions.
4. Check **Active Experiments** — review any experiments with kill/pause/scale rulings.
   - End experiments that have been killed.
   - Add notes to explain any decision you make.
5. Record a daily **Snapshot** for each active experiment (Snapshots page).
6. Review the **Trend** page for any experiment that has been running > 7 days.
7. Act on any approval that was approved: go to **Live Data** → execute (dry-run first).

---

## 3. Common operator tasks

| Task | Steps | Expected result | If it fails |
|---|---|---|---|
| Record a daily snapshot | Snapshots page → fill form → Submit | Row appears in the date table | Check the API is running; check the experiment ID matches exactly |
| Approve a pending action | Approval Queue → click Approve → add note | Status changes to Approved | Refresh the page; check the API is running |
| End a dead experiment | Active Experiments → expand card → End experiment | Status badge changes to ended | Check the API; check `ended_at` is set in DB |
| Add a note to an experiment | Active Experiments → expand card → Notes section → type + Add | Note appears below | API must be running |
| Check operator preflight | `GET /operator/preflight` or check Overview | `safe_to_operate: true` | See preflight response for blockers |
| Run tests | `python -m pytest -q` | All passing | Check ruff errors first; then read the failing test |
| Deploy | Not automated yet — see `docs/DEPLOYMENT.md` | Version running on server | Roll back to last known-good commit |

---

## 4. Things Aidan must not do

- Never manually run an ad campaign outside the approval gate.
- Never manually edit the database to "fix" a snapshot — add a corrected snapshot instead.
- Never commit `.env` or any file with real API keys.
- Never execute a Stripe or Shopify write in dry_run=False mode without first confirming
  in the approval queue that the action was approved.
- Never delete a `logs/` file — rotate via the operator tools only.
- Never merge directly to `main` — all changes go through a PR.

---

## 5. Developer setup

### Local install

```bash
# Python backend
cd "C:/Users/Aidan/OneDrive/Desktop/E-Commerce Store/marketmind.site"
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -e ".[dev]"

# Frontend
cd desktop
npm install
```

### Environment variables (never paste real values here)

| Variable | Required? | Purpose | Example shape |
|---|---|---|---|
| `STRIPE_SECRET_KEY` | For live Stripe reads | Stripe API auth | `sk_live_...` or `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | For webhook endpoint | Verify webhook signatures | `whsec_...` |
| `SHOPIFY_SHOP_DOMAIN` | For Shopify reads | Store subdomain | `mystore.myshopify.com` |
| `SHOPIFY_ACCESS_TOKEN` | For Shopify reads | Admin API token | `shpat_...` |
| `SHOPIFY_WEBHOOK_SECRET` | For webhook endpoint | Verify webhook signatures | Any string |
| `MARKETMIND_API_TOKEN` | Optional | Auth for the FastAPI backend | Any secure string |
| `DATABASE_URL` | Optional | Override DB path | `sqlite:///./data/marketmind.db` |

Copy `.env.example` to `.env` and fill in real values locally. Never commit `.env`.

### Run commands

```bash
# Start API (from repo root)
uvicorn marketmind.api.app:app --reload --port 8000

# Start desktop app (from desktop/)
npm run dev

# Run all tests
python -m pytest -q

# Lint
python -m ruff check .

# Alembic migration
alembic upgrade head
```

### Rollback

```bash
git log --oneline -10          # find the last good commit
git checkout <sha> -- .        # restore files (do not push until confirmed working)
python -m pytest -q            # verify
```

---

## 6. Health checks

| Check | How | Healthy | Unhealthy |
|---|---|---|---|
| API running | `GET /health` returns `{status: "ok"}` | `status: ok` | Server not running |
| Operator preflight | `GET /operator/preflight` | `safe_to_operate: true` | See `blockers` list |
| Tests | `python -m pytest -q` | All passing | Fix ruff, then failing tests |
| Pending approvals | Approval Queue page or `/approvals/pending` | Empty or all reviewed | Stale approvals blocking execution |

Logs: `logs/operator_events.jsonl` — append-only record of every operator-logged event.

---

## 7. Decision log

| Date | Decision | Why | Alternatives considered | Owner |
|---|---|---|---|---|
| 2026-06-16 | Slice-based build: one PR per feature | Keeps CI clean; each slice is independently testable | Big-bang build | Aidan |
| 2026-06-16 | SQLite for local dev; alembic for migrations | Simple; swappable to Postgres later | Postgres from day 1 | Aidan |
| 2026-06-16 | Approval gate is DB-backed, not file-based | Survives restart; queryable | JSONL file | Aidan |
| 2026-06-23 | Adopted Parts-and-Pieces utilities | Reuse proven patterns; avoid one-off logic | Custom implementations | Aidan |

---

## 8. Known risks and watch items

| Risk | Impact | Mitigation | Next action |
|---|---|---|---|
| Dry-run flag accidentally set to False | Real money spent without intent | All execution defaults to `dry_run=True`; approval required before any real run | Add test that default is dry_run=True |
| Stripe/Shopify key leaked in log | Security incident | Logs must never print raw env vars; `.env` is gitignored | Audit log output before adding new logging |
| DB grows unbounded | Disk full on VPS | Snapshots are pruned-by-date queries; no explicit rotation yet | Add snapshot rotation script |
| Experiment ID collision | Wrong data merged | experiment_id is the primary key; POST /snapshots creates or updates | Document ID naming convention in AGENTS.md |

---

## 9. Parts-and-Pieces parts used

| Part | Source | How used in MarketMind | Local file |
|---|---|---|---|
| `event_ledger` | `parts/python/event_ledger` | Operator audit log at `logs/operator_events.jsonl` | `marketmind/event_ledger.py` |
| `approval_policy` | `parts/python/approval_policy` | Commerce-specific HIGH_RISK_ACTIONS list + gate logic | `marketmind/commerce_approval_policy.py` |
| `checklist_gate` | `parts/python/checklist_gate` | Experiment scale-readiness checklist | `marketmind/experiment_checklist.py` |
| `operator_status` | `parts/python/operator_status` | Operator preflight: pending approvals + experiments needing action | `marketmind/operator_preflight.py` |
| `commerce_operator_os` blueprint | `docs/blueprints/commerce_operator_os.md` | Entire system architecture | This repo |
| `AGENTS.md` template | `docs/templates/AGENTS.md` | AI/dev agent instructions | `AGENTS.md` |
| `OWNER_MANUAL` template | `docs/templates/OWNER_MANUAL_AND_ISSUE_LOG.md` | This file | `OWNER_MANUAL.md` |
| `OPERATING_INDEX` template | `docs/templates/OPERATING_INDEX.md` | Navigation front door | `OPERATING_INDEX.md` |

---

## 10. Final handoff checklist

- [x] Owner can explain what the project does.
- [x] Owner can run normal tasks using this manual.
- [x] Developer can install and run locally.
- [x] Developer can run tests.
- [ ] Developer can deploy (deployment docs partially complete — see `docs/DEPLOYMENT.md`).
- [ ] Developer can roll back (rollback tested locally, not on VPS).
- [x] Important logs are documented.
- [ ] Known issues and fixes are dated in `docs/issues/`.
- [ ] Regression tests exist for all important fixed issues.
- [ ] Reusable parts returned to Parts & Pieces (pending review).
