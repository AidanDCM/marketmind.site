# MarketMind Autopilot Project Brief

## Plain-English summary

MarketMind Autopilot is a human-in-the-loop commerce operator. It should research ecommerce niches, find product opportunities, calculate unit economics, generate offer/store specs, prepare Codex build tasks, monitor performance, and queue risky actions for approval.

The goal is not to make Aidan manually operate an ecommerce store. The goal is to build a controlled operating system where the bot performs the daily work, Codex maintains the software, and Aidan approves important actions.

## Target user

Primary user: Aidan, acting as the owner/operator.

Secondary users:

- Codex or AI coding agents maintaining the codebase
- future collaborators reviewing product/niche tests
- future operators who may run the same system against other niches

## Main pain point

Starting ecommerce manually is risky, time-consuming, and easy to lose money on. Most beginners fail because they build stores before proving demand, do not understand unit economics, spend on ads too early, and do not kill losing offers fast enough.

MarketMind should reduce that risk by making product selection, pricing, P&L, launch tests, approvals, and learning systematic.

## Business outcome

Create a reusable commerce engine that can repeatedly test niche/product ideas until at least one proves profitable.

A profitable niche means:

```text
contribution profit after shipping, fees, refunds, and ad spend > 0
repeatable acquisition channel exists
fulfillment and support are manageable
refund/return rate stays within acceptable limits
```

## Success metrics

### System success

- Bot can ingest product/supplier/market data into normalized records.
- Bot can calculate break-even CAC and safe CAC for each offer.
- Bot can generate Codex-ready store and landing-page specs.
- Bot can produce daily P&L and kill/scale recommendations.
- Bot can queue approval-required actions instead of acting silently.
- Every decision is logged with enough evidence to replay and debug.

### Business success

- First validated offer reaches at least 3 real purchases or paid preorders.
- First serious test stays inside a pre-approved loss cap.
- At least one niche reaches positive contribution profit after ad spend.
- Losing products are killed before they burn uncontrolled cash.

## MVP scope

MVP means the smallest version that can safely test one product/niche idea.

MVP includes:

1. Commerce math engine
2. Product/opportunity record schema
3. Explainable product scoring
4. P&L model
5. Kill/scale rules
6. Landing-page/store spec generator
7. Approval policy and approval queue shape
8. Daily report output
9. Codex handoff format
10. Static public landing page

## Later scope

- Shopify adapter
- Stripe Payment Links adapter
- WooCommerce/Medusa/Saleor adapters
- TikTok Shop/marketplace adapters
- ad platform report importers
- supplier API adapters
- customer support assistant
- automated content brief generation
- dashboard UI
- multi-niche experiment runner
- pp_brain domain pack
- MCP tools for commerce operations

## Non-goals

MarketMind should not initially:

- run uncapped paid ads
- auto-publish products without approval
- auto-order inventory without approval
- auto-send customer/supplier messages without approval
- issue refunds without approval
- fake reviews, fake urgency, fake identity, or misleading claims
- scrape protected/paywalled/login/CAPTCHA systems
- become a giant uncontrolled agent

## Assumptions

- Aidan wants to remain the human approver, not the manual store operator.
- Codex will be used to build and maintain code.
- Early store tests should protect cash and avoid inventory risk.
- Stripe Payment Links or simple landing pages may be used before Shopify.
- Shopify is useful after a winning offer is validated.
- The bot must be reusable across niches.

## Open questions

- Which platform should be first for checkout: Stripe Payment Links, Shopify, Payhip, WooCommerce, Medusa, or Saleor?
- Which first niche should be tested: daily driver car kits, travel kits, pet/home cleaning, creator desk setups, or another niche?
- What is the first approved test budget?
- Which ad platform is allowed first, if any?
- What exact approval UI should V1 use: CLI, GitHub issues, Streamlit, local dashboard, or web dashboard?

## First recommended niche

Daily Driver Upgrade Kits.

Reason: it matches Aidan's existing interests in cars, comfort, commuting, old interiors, Miami heat, road conditions, and practical upgrades. This gives the operator better taste and judgment than a random niche.

Initial product ideas:

- interior refresh kit
- Miami heat car kit
- daily commuter comfort kit
- rideshare driver upgrade kit
- old car organization and comfort kit

Avoid early:

- electronics
- lithium batteries
- safety-critical tools
- heavy products
- products requiring complex installation
