# MarketMind Autopilot Architecture

## Architecture goal

Build a safe, modular commerce operator that can research, score, test, and operate ecommerce experiments while keeping risky actions approval-gated.

The system should be boring where possible, modular where necessary, and observable everywhere.

## High-level system

```text
Public Landing Page
  -> explains MarketMind and its safety stance

Operator Dashboard / CLI
  -> shows Today, Approvals, P&L, Products, Niches, Ads, Orders, Logs

MarketMind Backend
  -> product research
  -> opportunity scoring
  -> unit economics
  -> offer/store spec generation
  -> approvals
  -> logs
  -> reports

Commerce Brain Domain Pack
  -> receives state, goals, tools, and rules
  -> returns structured decisions
  -> never executes high-risk actions directly

Integrations
  -> Stripe Payment Links
  -> Shopify
  -> WooCommerce / Medusa / Saleor later
  -> supplier data sources
  -> ad analytics imports
  -> GitHub/Codex task creation
```

## Recommended initial stack

### V1

- Static site: existing `index.html`
- Backend: Python FastAPI or simple Python CLI first
- Database: SQLite first
- Logs: JSONL event logs
- Dashboard: Streamlit or lightweight web dashboard later
- Store validation: Stripe Payment Links + static landing pages first
- Store scale: Shopify after demand is proven

### Later

- Postgres
- Redis/job queue
- pp_brain domain pack
- MCP tool gateway
- Shopify Admin API
- ad platform report importers
- supplier API adapters
- dashboard deployment

## Core modules

### 1. Research Engine

Responsibilities:

- collect niche ideas
- collect competitor data
- collect supplier/product data
- collect review and community pain points
- separate verified evidence from guesses

Inputs:

- manual seed ideas
- CSV exports
- supplier files
- public research notes
- marketplace/product snapshots

Outputs:

- normalized `NicheCandidate`
- normalized `ProductCandidate`
- normalized `SupplierCandidate`
- evidence records

### 2. Product/Item Finder

Responsibilities:

- scan candidate products
- detect product patterns
- identify bundle opportunities
- avoid products with dangerous risk profiles

Scoring dimensions:

- margin potential
- shipping cost and weight
- return/refund risk
- content/demo potential
- supplier reliability
- competition intensity
- repeat purchase potential
- platform fit
- personal fit for Aidan

### 3. Commerce Math Engine

Responsibilities:

- calculate product contribution profit
- calculate break-even CAC
- calculate safe CAC
- estimate P&L
- apply kill/scale rules

Core formula:

```text
revenue
- product cost
- shipping cost
- packaging cost
- platform/payment fees
- return/damage allowance
- ad cost
= contribution profit
```

No product should proceed to paid testing without a known break-even CAC.

### 4. Offer Engine

Responsibilities:

- create bundle plans
- generate pricing options
- define free-shipping threshold
- draft product page specs
- draft landing page specs
- draft FAQ and policy copy
- define analytics events

Output:

- `OfferSpec`
- `LandingPageSpec`
- `StoreSpec`
- `CodexBuildTask`

### 5. Store Builder / Codex Handoff

Responsibilities:

- transform specs into Codex-ready tasks
- require tests and acceptance criteria
- prevent Codex from building randomly from raw ideas
- create GitHub issues or handoff documents

Codex should build one testable slice at a time.

### 6. Operations Engine

Responsibilities:

- import orders
- import refunds
- import ad reports
- import product performance
- monitor inventory/supplier state
- generate daily operating reports

Initial mode should be read-only.

### 7. Approval Engine

Responsibilities:

- classify action risk
- auto-allow safe actions
- queue high-risk actions
- block prohibited actions
- log all decisions

Critical actions require human approval.

### 8. Learning Engine

Responsibilities:

- compare recommendations to outcomes
- extract lessons
- update scorecards
- write regression cases for failures
- improve future product/niche tests

## Data ownership

SQLite is the V1 source of truth.

Recommended tables:

- `niches`
- `products`
- `suppliers`
- `evidence_records`
- `scores`
- `offers`
- `experiments`
- `approvals`
- `orders`
- `ad_reports`
- `pnl_snapshots`
- `events`
- `lessons`

## Decision object

Every bot decision should be structured.

```json
{
  "decision_type": "suggest | request_approval | block | learn_only",
  "action": "short_machine_action",
  "risk_level": "low | medium | high | critical",
  "requires_approval": true,
  "confidence": 0.78,
  "evidence_ids": [],
  "reason_summary": "Short explanation, not hidden reasoning.",
  "expected_impact": {
    "revenue": 0,
    "cost": 0,
    "profit": 0
  },
  "rollback_plan": "How to undo or stop this action.",
  "blocked": false,
  "block_reason": null
}
```

## Risk levels

### Low

- read-only analytics
- calculations
- internal draft generation
- internal scoring
- daily reports

### Medium

- create product draft
- create unpublished page draft
- create GitHub issue
- create internal support draft

### High

- publish product
- launch ad
- increase budget
- change live price
- send external message
- create payment link

### Critical

- uncapped spend
- credential access
- refunds
- payment/account settings
- inventory purchases
- destructive data deletion

Critical actions must not run silently.

## Initial platform ladder

1. Static landing pages + Stripe Payment Links
2. Shopify once validated
3. WooCommerce / Medusa / Saleor for owned open-source control later
4. TikTok Shop / eBay / Etsy / Amazon only after compliance review

## Observability

Minimum logs:

- event input
- state summary
- decision
- risk classification
- evidence used
- approval status
- execution result
- P&L impact
- lesson extracted

## Security model

- No secrets in repo
- Use `.env` locally
- Use least-privilege API scopes
- Start all integrations as read-only
- Require approval for write actions
- Mask sensitive values in logs
- Keep destructive actions disabled in V1

## Deployment model

### Now

- Static site only

### V1 application

- local CLI or Streamlit dashboard
- SQLite database
- JSONL logs
- local `.env`

### Later

- FastAPI backend
- Postgres
- background worker
- approval dashboard
- cloud deployment
