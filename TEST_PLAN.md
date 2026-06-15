# MarketMind Autopilot Test Plan

## Testing philosophy

MarketMind is a money-adjacent automation system. A bug can waste cash, publish bad products, send bad messages, or create compliance problems. Testing is not optional.

The system must prove:

- math is correct
- approvals work
- risky actions are blocked
- unknowns are not treated as facts
- external integrations start read-only or dry-run
- failures are logged and recoverable

## Test categories

## 1. Unit tests

### Commerce math engine

Test cases:

- profitable product with safe CAC
- break-even product
- losing product before ads
- losing product after ads
- high shipping cost
- high refund allowance
- zero price
- missing product cost
- negative or invalid inputs

Expected behavior:

- invalid inputs fail validation
- break-even CAC is calculated correctly
- safe CAC is lower than break-even CAC
- products with weak margin are flagged

### Product scoring

Test cases:

- high-margin lightweight product
- low-margin product
- heavy product
- fragile product
- regulated/unsafe product
- product with missing evidence
- product with supplier risk

Expected behavior:

- score includes reasons
- score includes risk flags
- missing evidence lowers confidence
- prohibited products are blocked or marked non-goal

### Approval policy

Test cases:

- low-risk read-only action
- medium-risk draft action
- high-risk live publish action
- critical spend/refund/credential action
- unknown action type

Expected behavior:

- low-risk actions can be auto-allowed
- high-risk actions require approval
- critical actions are blocked unless explicitly enabled
- unknown actions are blocked

## 2. Integration tests

### Source adapter tests

- import product CSV
- import supplier CSV
- import ad report CSV
- import order export CSV
- handle bad column names
- handle missing required fields

Expected behavior:

- valid rows normalize into internal records
- invalid rows go to review queue
- failed imports do not crash the whole run

### Payment/store adapter tests

V1 must be dry-run first.

- Stripe Payment Link request payload builds correctly
- Shopify product draft payload builds correctly
- live mode fails without approval
- secrets are never printed
- API errors are logged safely

## 3. Regression tests

Create regression tests whenever:

- the bot recommends a losing scale action
- a product is approved with bad math
- an approval gate fails
- bad input crashes the run
- a misleading claim is generated
- an external message is sent incorrectly
- a product with missing evidence is marked verified

## 4. Safety tests

Required safety tests:

- unknown tool is blocked
- unknown action is blocked
- critical action requires approval
- budget cap cannot be exceeded silently
- credentials are masked in logs
- no `.env` values are committed
- no fake review generation is allowed
- no protected scraping action is allowed

## 5. P&L tests

Test scenarios:

### Scenario A: organic profitable product

- AOV: 59
- product cost: 18
- shipping: 8
- fees: 3
- refund allowance: 2
- CAC: 0

Expected: profitable.

### Scenario B: paid ads still profitable

- same as Scenario A
- CAC: 14

Expected: profitable, safe to continue.

### Scenario C: ad spend breaks the offer

- same as Scenario A
- CAC: 35

Expected: losing, pause/kill recommendation.

### Scenario D: heavy product

- AOV: 49
- product cost: 12
- shipping: 22
- fees: 3
- refund allowance: 3
- CAC: 10

Expected: high shipping risk, do not scale.

## 6. Manual verification checklist

Before any release:

```text
[ ] Static site still loads
[ ] README explains the product clearly
[ ] No secrets committed
[ ] All new docs are linked from README
[ ] P&L examples are realistic
[ ] Approval policy blocks risky actions
[ ] Codex handoff is clear
[ ] First build slice is small and testable
```

Before any live commerce integration:

```text
[ ] Integration has dry-run mode
[ ] Integration has read-only mode where possible
[ ] Credentials are loaded from environment only
[ ] Write actions require approval
[ ] Logs mask sensitive values
[ ] Rollback or disable path exists
```

## 7. Test command targets

When the Python app exists, add commands like:

```bash
python -m pytest
python -m pytest tests/test_math_engine.py
python -m pytest tests/test_approvals.py
python -m marketmind.cli doctor
python -m marketmind.cli run-dry-run
```

## 8. Minimum acceptance before V1 launch

V1 is not launchable until:

- commerce math engine tests pass
- approval tests pass
- source adapter tests pass
- no secret scan warnings exist
- dry-run payment/store flows are verified
- daily report can be generated from sample data
- losing-product examples are correctly rejected
