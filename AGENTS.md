# AGENTS.md — Instructions for AI Coding Agents and Developers

This file is at the repo root so any AI agent or developer sees it before touching code.

## Before changing anything, read in order

1. `README.md` — what MarketMind Autopilot is and why it exists
2. `SLICE_WORKFLOW.md` — slice building vs system hardening; testing microscope; engineering log
3. `OWNER_MANUAL.md` — how to run, test, deploy, and roll back the system
4. `OPERATING_INDEX.md` — navigation map of every major doc and system area
5. `docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md` — commands and evidence rules
6. `ARCHITECTURE.md` — system layout, layer boundaries, DB schema
7. `docs/issues/` — known failures and fixes (read before introducing similar changes)
8. `docs/engineering_log/` — forensic ledger of past changes (read before repeating mistakes)
9. `CHANGELOG.md` — slice summary (what changed recently)

Then confirm: you understand the approval gate, the experiment lifecycle, the DB models,
the test suite structure, and the high-risk action list before editing anything.

## Slice workflow (binding)

When Aidan says **`proceed`** during Phase A (slice building):

1. Implement **one** testable slice (Overview link, operator panel, API, etc.).
2. Run **microscope testing** — full suite plus focused tests for touched modules;
   desktop Vitest + build when `desktop/` changes. See `SLICE_WORKFLOW.md`.
3. Update `CHANGELOG.md`, `OPERATING_INDEX.md` slice counter, and add
   **`docs/engineering_log/YYYY-MM-DD-<slug>.md`** in the **same PR** (verbose: why,
   where, when, commands + exit codes).
4. Commit → push → PR → merge → sync `main` (unless Aidan says otherwise).

When slice roadmap is **complete**, **`proceed`** enters **Phase B** (system hardening):
each turn tests deeply, improves gaps, or rebuilds broken parts — see
`.agents/skills/testing-marketmind-system/SKILL.md`. Still log every pass in
`docs/engineering_log/`.

## Testing discipline (non-negotiable)

- **512+** backend pytest cases and **28+** desktop Vitest files — every behavior
  change adds a regression test naming the failure it prevents.
- Run `python -m ruff check .` and `python -m pytest -q` before every merge.
- When touching UI: `cd desktop && npm test && npm run build`.
- Record evidence in engineering log and optionally `python scripts/local_ci.py`
  (appends `reports/local_ci/TEST_LOG.md`).
- Never claim "tests passed" without command output. Never weaken tests to go green.

## Audit triad (when adding recurring analyses)

See `docs/audits/README.md`: tool + runbook + committed report per run.

## Prime directive

MarketMind is a human-in-the-loop commerce operator. It must never silently spend money,
change live prices, publish product pages, contact suppliers, or take any other high-risk
action without an explicit human approval record in the database. This is not a preference —
it is a hard system invariant. Every code change must preserve it.

## Non-negotiable rules

- Do not make changes until you understand the OWNER_MANUAL, test commands, known issues,
  rollback path, and the approval gate system.
- Keep changes small, focused, and test-backed. Every new behavior gets a regression test.
- Preserve existing behavior unless the task explicitly requires changing it.
- Never commit secrets, API keys, `.env` files, local databases, generated logs,
  private screenshots, or personal runtime artifacts.
- Never bypass the approval gate. `ApprovalStatus.PENDING` actions must not be executed.
- Never write directly to Stripe, Shopify, or any external paid service from test code.
  All external calls must use the dry-run path or a fake/stubbed client.
- Update `docs/issues/` when you discover, investigate, or fix a meaningful issue.
- Update `OWNER_MANUAL.md` when install, run, test, deploy, or rollback instructions change.
- Prefer reusing `marketmind/` utilities (event_ledger, commerce_approval_policy,
  experiment_checklist, operator_preflight, mistake_tracker) before creating new one-off logic.

## High-risk actions — always require an approved ApprovalRow before execution

| Action | Why it's high-risk |
|---|---|
| `launch_ad_campaign` | Real money leaves the account |
| `scale_ad_spend` | Real money leaves the account |
| `pause_ad_campaign` | Affects live revenue |
| `kill_experiment` | Irreversible campaign termination |
| `publish_product_page` | Public-facing content change |
| `change_product_price` | Affects all live visitors instantly |
| `contact_supplier` | Commits Aidan to a business relationship |
| `send_payment_link` | Triggers real payment request |
| `change_payment_settings` | Financial account change |
| `override_experiment_ruling` | Bypasses the rule engine |

Low-risk work (research, scoring, drafts, reports, snapshots) is automatic.
Medium-risk work (offer specs, Codex handoffs, forecasts) is draft-only until approved.
Critical actions (hiding losses, deleting logs, bypassing policies) are blocked in code.

## Required format for non-trivial fixes

Every non-trivial fix must record in `docs/issues/`:

- symptom
- context / when it appeared
- root cause
- failed attempts
- working solution
- files changed
- tests added or updated
- reusable lesson

## Definition of done

A task is not done until: code, tests, **engineering log entry** (`docs/engineering_log/`),
`CHANGELOG` entry (if a slice), `OWNER_MANUAL` (if ops changed), and issue log (if a bug
was fixed) are all consistent and passing CI / local_ci evidence.

## Experiment ID convention

All experiment IDs must match `exp_<slug>`: lowercase letters, digits, underscores, and
hyphens only (e.g. `exp_interior_kit`, `exp_test_01`). The API rejects invalid IDs on
snapshot submit. Never reuse an ID for a different product — end the old experiment first.

## Parts-and-Pieces origin

This repo was built using patterns from `Parts-and-Pieces`. The following utilities
were adopted and adapted for MarketMind:

- `parts/python/event_ledger` → `marketmind/event_ledger.py`
- `parts/python/approval_policy` → `marketmind/commerce_approval_policy.py`
- `parts/python/checklist_gate` → `marketmind/experiment_checklist.py`
- `parts/python/operator_status` → `marketmind/operator_preflight.py`
- `docs/blueprints/commerce_operator_os.md` → `ARCHITECTURE.md` + this repo
- `docs/templates/AGENTS.md` → this file
- `docs/templates/OWNER_MANUAL_AND_ISSUE_LOG.md` → `OWNER_MANUAL.md`
- `docs/templates/OPERATING_INDEX.md` → `OPERATING_INDEX.md`

If a new reusable pattern is developed here, document whether it should be returned
to `Parts-and-Pieces` before closing the PR.
