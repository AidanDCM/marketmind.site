# AGENTS.md — Instructions for AI Coding Agents and Developers

This file is at the repo root so any AI agent or developer sees it before touching code.

## Before changing anything, read in order

1. `README.md` — what MarketMind Autopilot is and why it exists
2. `OWNER_MANUAL.md` — how to run, test, deploy, and roll back the system
3. `OPERATING_INDEX.md` — navigation map of every major doc and system area
4. `ARCHITECTURE.md` — system layout, layer boundaries, DB schema
5. `docs/issues/` — known failures and fixes (read before introducing similar changes)
6. `CHANGELOG.md` — what changed recently and why

Then confirm: you understand the approval gate, the experiment lifecycle, the DB models,
the test suite structure, and the high-risk action list before editing anything.

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
  experiment_checklist, operator_preflight) before creating new one-off logic.

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

A task is not done until: code, tests, CHANGELOG entry, OWNER_MANUAL (if ops changed),
and issue log (if a bug was fixed) are all consistent and passing CI.

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
