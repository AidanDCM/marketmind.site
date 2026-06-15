# MarketMind Autopilot Development Plan

## Build rule

Do not build the whole system at once. Build one independently testable slice at a time.

The first objective is to create a safe experiment runner, not a fully autonomous store.

## Slice 1: Commerce math engine

### Goal

Create the financial calculator that prevents bad product decisions.

### User value

Aidan can see whether a product can survive shipping, fees, returns, and ad costs before any money is spent.

### Files likely affected

```text
marketmind/
  math_engine.py
  schemas.py
  rules.py
tests/
  test_math_engine.py
```

### Implementation steps

1. Define `ProductCostInput` schema.
2. Define `UnitEconomicsResult` schema.
3. Implement contribution profit calculation.
4. Implement break-even CAC.
5. Implement safe CAC target.
6. Implement margin and risk flags.
7. Add tests for profitable, break-even, and losing products.

### Acceptance criteria

- Calculates net profit before ads.
- Calculates break-even CAC.
- Flags products that cannot support ads.
- Does not call any external API.
- Tests cover edge cases like zero price, high shipping, and negative margin.

### Rollback plan

Disable or remove the module without affecting the static site.

## Slice 2: Product/opportunity schema

### Goal

Create normalized records for products, suppliers, niches, and evidence.

### User value

The bot can compare products from different sources without messy vendor-specific fields.

### Files likely affected

```text
marketmind/schemas.py
tests/test_schemas.py
```

### Acceptance criteria

- `ProductCandidate` validates required fields.
- `SupplierCandidate` validates required fields.
- `EvidenceRecord` requires source name and confidence.
- Unknown claims cannot be marked verified.

## Slice 3: Explainable product scoring

### Goal

Score product candidates with reasons, points, risks, and confidence.

### User value

Aidan sees why the bot likes or rejects a product.

### Files likely affected

```text
marketmind/scoring.py
marketmind/rules.py
tests/test_scoring.py
```

### Acceptance criteria

- Score includes criteria breakdown.
- Score includes risk summary.
- Score includes confidence level.
- Score does not treat missing evidence as verified.

## Slice 4: Kill/scale rule engine

### Goal

Create hard business rules that decide whether to stop, continue, revise, or scale a product test.

### User value

The bot cannot keep burning money because it is optimistic.

### Files likely affected

```text
marketmind/experiment_rules.py
tests/test_experiment_rules.py
```

### Acceptance criteria

- Pauses if CAC exceeds break-even.
- Flags weak conversion rate.
- Flags low add-to-cart rate.
- Blocks scale recommendations without profit signal.
- Returns a clear reason and recommended next action.

## Slice 5: Landing-page and offer spec generator

### Goal

Generate Codex-ready specs for a simple product validation page.

### User value

Codex can build from a clear spec instead of guessing.

### Files likely affected

```text
marketmind/spec_generator.py
marketmind/templates/
tests/test_spec_generator.py
```

### Acceptance criteria

- Generates product headline.
- Generates bundle breakdown.
- Generates FAQ.
- Generates CTA plan.
- Generates analytics event list.
- Does not make fake claims.

## Slice 6: Approval queue shape

### Goal

Create a local approval record model and CLI/dashboard output.

### User value

Aidan can approve or deny risky actions while the bot still does the work.

### Files likely affected

```text
marketmind/approvals.py
marketmind/cli.py
tests/test_approvals.py
```

### Acceptance criteria

- Low-risk actions can be auto-approved.
- High-risk actions require approval.
- Critical actions are blocked unless explicitly enabled.
- Every approval has a timestamp, reason, and rollback plan.

## Slice 7: Read-only analytics/import layer

### Goal

Import CSV or API-exported data into internal records.

### User value

The bot can monitor performance without write permissions.

### Files likely affected

```text
marketmind/source_adapters.py
marketmind/importers.py
tests/test_importers.py
```

### Acceptance criteria

- Can import product candidates from CSV.
- Can import ad reports from CSV.
- Can import order summaries from CSV.
- Bad files go to review instead of crashing.

## Slice 8: Daily report generator

### Goal

Generate a daily operator report.

### User value

Aidan sees what happened, what matters, and what needs approval.

### Files likely affected

```text
marketmind/reports.py
tests/test_reports.py
```

### Acceptance criteria

Report includes:

- revenue
- ad spend
- contribution profit
- CAC
- conversion rate
- refunds
- approval queue
- kill/scale recommendations
- lessons learned

## Slice 9: Stripe Payment Links adapter

### Goal

Add approval-gated checkout creation.

### User value

The bot can prepare payment links for validation offers.

### Important rule

Start as dry-run only. Live creation requires approval.

### Acceptance criteria

- Dry-run creates a request payload.
- Live mode requires approval.
- No secret keys are logged.

## Slice 10: Shopify adapter

### Goal

Add Shopify read-only first, write actions later.

### User value

MarketMind can graduate from landing-page validation to real store operations.

### Acceptance criteria

- Read products/orders in read-only mode.
- Draft product creation requires approval.
- Publishing requires approval.
- Price changes require approval.

## Milestone targets

### Milestone 1: Safe local calculator

Includes slices 1-4.

### Milestone 2: Spec generator and approval layer

Includes slices 5-6.

### Milestone 3: Read-only operator loop

Includes slices 7-8.

### Milestone 4: Controlled commerce integrations

Includes slices 9-10.

## Definition of done per slice

- Acceptance criteria satisfied
- Tests added or updated
- Relevant tests pass
- Errors and edge cases handled
- No secrets committed
- Documentation updated
- Rollback or disable path understood
