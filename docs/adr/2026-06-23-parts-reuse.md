# ADR: 2026-06-23 — Parts-and-Pieces Integration for MarketMind

**Status:** Implemented  
**Author:** Aidan  
**Adapted from:** `docs/templates/parts_reuse_decision_adr.md` (Parts-and-Pieces)

---

## Context

MarketMind Autopilot was built slice-by-slice with custom implementations of
several patterns that are available in reusable form from `Parts-and-Pieces`.
As the codebase matures, we should replace or augment one-off logic with the
proven, tested patterns from the shared library.

This ADR records which parts were evaluated and what decision was made for each.

---

## Candidate Parts-and-Pieces modules reviewed

| Part | Adopt | Defer | Skip | Reason |
|---|:---:|:---:|:---:|---|
| `parts/python/event_ledger` | ✓ | | | MarketMind needs an append-only operator audit log; this is exactly it |
| `parts/python/approval_policy` | ✓ | | | Defines the HIGH_RISK_ACTIONS list; adapted with commerce-specific actions |
| `parts/python/checklist_gate` | ✓ | | | Experiment scale-readiness gate fits the existing experiment lifecycle |
| `parts/python/operator_status` | ✓ | | | Preflight check maps cleanly to pending approvals + attention rulings |
| `parts/python/decision_gate` | | ✓ | | Already implemented as the approvals system; wire at next opportunity |
| `parts/python/mistake_tracker` | | ✓ | | Useful for experiment lessons; defer until experiment notes are established |
| `parts/python/blackout_calendar` | | | ✓ | Trading-specific; no clear commerce ad-schedule use case yet |
| `parts/python/reconciliation` | | | ✓ | Approval DB already handles state consistency; not needed at this scale |
| `parts/python/reward_tracker` | | | ✓ | Not applicable to commerce ops |
| `parts/python/loop_detector` | | | ✓ | No long-running agent loops in MarketMind yet |
| `parts/python/signal_engine` | | | ✓ | Guarded trading part; not applicable |
| `parts/python/source_adapters` | | | ✓ | Shopify/Stripe importers are already built |
| `parts/python/gmail_draft_client` | | ✓ | | No email outreach workflow yet; defer to outreach slice |
| `docs/blueprints/commerce_operator_os.md` | ✓ | | | This repo is the implementation of that blueprint |
| `docs/templates/AGENTS.md` | ✓ | | | Adapted as `AGENTS.md` |
| `docs/templates/OWNER_MANUAL_AND_ISSUE_LOG.md` | ✓ | | | Adapted as `OWNER_MANUAL.md` |
| `docs/templates/OPERATING_INDEX.md` | ✓ | | | Adapted as `OPERATING_INDEX.md` |
| `parts/typescript/operator-health-panel` | | ✓ | | Could become the Overview dashboard; defer |
| `parts/typescript/order-lifecycle` | | ✓ | | Could structure the Shopify order flow; defer |

---

## Decision

**Adopt immediately:**
- `event_ledger` → `marketmind/event_ledger.py` + `GET /operator/preflight`, `POST /operator/log-event`
- `approval_policy` → `marketmind/commerce_approval_policy.py`
- `checklist_gate` → `marketmind/experiment_checklist.py` + `GET /experiment/{id}/checklist`
- `operator_status` → `marketmind/operator_preflight.py`
- All three doc templates → `AGENTS.md`, `OWNER_MANUAL.md`, `OPERATING_INDEX.md`

**Defer:**
- `decision_gate`, `mistake_tracker`, `gmail_draft_client`, `operator-health-panel`, `order-lifecycle`

**Skip:**
- All others (see table above)

---

## Why this is better than custom code

- These parts were extracted from working systems and have tests.
- The checklist gate pattern is safer than ad-hoc ruling checks in the UI.
- The event ledger gives us a durable, replayable operator audit trail with zero schema migration cost.
- The operator preflight consolidates three different "is the system safe?" checks into one endpoint.
- The approval policy codifies the HIGH_RISK_ACTIONS list in one file, making it easy to audit and extend.

---

## Integration plan

1. ✓ Copy and adapt `event_ledger` → `marketmind/event_ledger.py`
2. ✓ Copy and adapt `approval_policy` → `marketmind/commerce_approval_policy.py`
3. ✓ Copy and adapt `checklist_gate` → `marketmind/experiment_checklist.py`
4. ✓ Copy and adapt `operator_status` → `marketmind/operator_preflight.py`
5. ✓ Wire into `marketmind/api/routers/operator.py` and `experiments.py`
6. ✓ Register `operator` router in `app.py`
7. ✓ Write tests for all new endpoints
8. ✓ Adapt doc templates into `AGENTS.md`, `OWNER_MANUAL.md`, `OPERATING_INDEX.md`

---

## Risks

- **API mismatch:** The parts use generic field names; MarketMind-specific names are
  in the wrappers, not the parts themselves. If the parts are updated upstream, the
  wrapper logic may need to be reviewed.
- **Event ledger file path:** Defaults to `logs/operator_events.jsonl` relative to CWD.
  In Docker/VPS deployments, ensure the working directory is correct or override the path.
- **Checklist thresholds:** The scale-readiness thresholds (min 100 visits, 5 orders,
  $50 spend) are hardcoded. These should be configurable from env vars in a future slice.

---

## Return-to-library obligation

If MarketMind improves any of these patterns (e.g., the checklist gate gains
experiment-specific threshold config, or the preflight adds more checks), those
improvements should be documented and the option to return them to Parts-and-Pieces
should be evaluated before closing the next major PR.
