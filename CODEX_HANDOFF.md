# Codex Handoff: MarketMind Autopilot

## Required acknowledgement

Before coding, Codex or any developer must acknowledge:

```text
I have read the MarketMind README, PROJECT_BRIEF.md, ARCHITECTURE.md, DEVELOPMENT_PLAN.md, TEST_PLAN.md, APPROVAL_POLICY.md, and PNL_MODEL.md.
I have read the Parts & Pieces Developer Operating System (AidanDCM/Parts-and-Pieces: AGENTS.md and DEVELOPER_OPERATING_SYSTEM.md).
I will build from a clear blueprint, one testable slice at a time.
I will check docs/decisions/0002-parts-and-pieces-reuse.md before building any new module.
I will not create live commerce, payment, ad, refund, inventory, or messaging actions without approval gates.
I will not commit secrets or .env files.
I will not invent requirements, hide uncertainty, or make unrelated changes.
I will stop after each slice and report before proceeding to the next.
```

## Parts & Pieces mandate

This project is built under the Parts & Pieces Developer Operating System.
See `docs/decisions/0002-parts-and-pieces-reuse.md` for the full reuse evaluation.

**Mandatory for upcoming slices:**

- **Slice 6 (approval queue):** use `parts/python/decision_gate/decision_gate.py`
  and `parts/python/checklist_gate/checklist_gate.py` — do not build a custom
  sequential approval runner.
- **Slice 7 (CSV imports):** use `parts/python/source_adapters/csv_source_adapter.py`
  — do not build a custom CSV normalizer.
- **Slice 7/8 (logging):** use `parts/python/event_ledger/jsonl_event_ledger.py`
  — do not build a custom JSONL logger.

Do not re-evaluate these decisions. They are already documented.

## Build objective

Create MarketMind Autopilot as a safe human-in-the-loop commerce operator.

The first version should not be a full autonomous Shopify store. It should be a local, testable commerce decision engine that can:

1. calculate product unit economics
2. score product opportunities
3. apply kill/scale rules
4. generate offer/store specs
5. queue approval-required actions
6. produce daily reports

## First slice to build

### Slice 1: Commerce math engine

Build a Python package skeleton:

```text
marketmind/
  __init__.py
  schemas.py
  math_engine.py
  rules.py
  cli.py

tests/
  test_math_engine.py
```

### Requirements

`schemas.py` should define:

- `ProductCostInput`
- `UnitEconomicsResult`
- `RecommendedAction`

`math_engine.py` should calculate:

- gross profit before ads
- break-even CAC
- safe CAC low/high
- estimated contribution profit
- margin status
- recommended action
- risk flags

`rules.py` should define:

- default safe CAC percentage range
- minimum gross margin rules
- high shipping risk rule
- negative contribution profit rule

`cli.py` should support a dry-run command like:

```bash
python -m marketmind.cli calc-sample
```

The command should print a sample unit economics result for a Daily Driver Interior Refresh Kit.

### Acceptance criteria

- No external API calls.
- No secrets.
- No payments.
- No Shopify/Stripe/ad integrations yet.
- Unit tests cover profitable, break-even, and losing examples.
- Tests can be run with `python -m pytest`.
- Invalid input is handled clearly.
- Output is structured and easy to log.

## Strong suggested implementation

Use Pydantic if the repo already has Python dependency structure. If not, use dataclasses first to avoid unnecessary dependency setup.

Prefer boring code.

Do not add web frameworks, dashboards, Shopify, Stripe, or agents in Slice 1.

## Prohibited in first slice

Do not build:

- Shopify integration
- Stripe integration
- ad platform integration
- dashboard UI
- crawler/scraper
- autonomous purchase system
- inventory order system
- customer messaging system
- LLM agent layer

The first slice is only math and rules.

## Future slices

After Slice 1 passes:

1. Add product/opportunity schemas.
2. Add explainable scoring.
3. Add kill/scale experiment rules.
4. Add offer and landing-page spec generator.
5. Add approval queue.
6. Add CSV/source imports.
7. Add daily report generator.
8. Add dry-run Stripe Payment Links adapter.
9. Add read-only Shopify adapter.
10. Add approval-gated write integrations.

## Safety reminders

Critical actions must remain blocked by default:

- real ad spend
- refunds
- account/payment changes
- inventory purchases
- customer/supplier messages
- live publishing
- credential access
- destructive deletion

## Recommended first sample input

```json
{
  "product_name": "Daily Driver Interior Refresh Kit",
  "sale_price": 59.0,
  "product_cost": 18.0,
  "packaging_cost": 1.5,
  "shipping_cost": 8.0,
  "platform_fee": 1.5,
  "payment_fee": 2.0,
  "refund_allowance": 2.0,
  "software_allocation": 0.5,
  "estimated_cac": 14.0
}
```

Expected output should classify this as a controlled test candidate if contribution profit is positive and the CAC is below the safe range.

## Completion report format

After the slice, report:

```text
Goal of slice:
What changed:
Files changed:
Tests added/updated:
Commands run:
Test results:
Manual verification:
Remaining risks:
Rollback/disable plan:
Next recommended slice:
```
