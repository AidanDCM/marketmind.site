# MarketMind Autopilot Approval Policy

## Purpose

MarketMind should do the work, but it should not silently take risky actions.

The approval policy exists to protect cash, customer trust, accounts, credentials, legal/compliance posture, and brand reputation.

## Core rule

```text
The bot may research, calculate, draft, recommend, and prepare.
The bot may not silently spend, publish, message, refund, order, delete, or change critical settings.
```

## Risk levels

## Low risk: automatic allowed

Low-risk actions may run automatically if they are logged.

Examples:

- read internal data
- read public pages that do not require login or bypass
- import user-provided CSVs
- calculate unit economics
- score products
- draft product copy internally
- draft ads internally
- draft customer replies internally
- generate reports
- create local logs
- create internal recommendations

Requirements:

- log event
- log output
- attach confidence/evidence where relevant

## Medium risk: automatic only in draft mode

Medium-risk actions can create drafts, never final external changes.

Examples:

- create unpublished product draft
- create unpublished landing-page draft
- create GitHub issue for Codex
- create internal ad brief
- create internal supplier email draft
- create internal customer support draft
- prepare payment link payload in dry-run mode

Requirements:

- mark as draft
- no external send/publish
- include rollback or delete plan
- queue for review if user-facing

## High risk: approval required

High-risk actions require explicit approval before execution.

Examples:

- publish a product
- publish a landing page
- create a live Stripe Payment Link
- launch an ad campaign
- increase ad spend
- change live product price
- change live shipping policy
- change live return policy
- send a customer message
- send a supplier message
- order product samples
- install a paid app
- export customer data

Requirements:

- approval record
- risk level
- expected cost
- expected upside
- rollback/disable plan
- confidence score
- evidence summary

## Critical risk: blocked by default

Critical-risk actions are blocked unless the system has an explicit manual override feature and Aidan has approved that action.

Examples:

- uncapped ad spend
- changing payment account settings
- accessing raw credentials
- issuing refunds
- deleting customer/order/product data
- ordering inventory at scale
- changing DNS/account ownership
- bypassing platform restrictions
- using fake reviews or fake identities
- scraping protected/paywalled/CAPTCHA/login-restricted systems
- making medical, legal, or safety claims without verified evidence

Requirements:

- blocked by default
- no silent execution
- manual approval required
- reason logged
- disable/rollback plan required

## Prohibited actions

MarketMind must never:

- fake reviews
- generate fake testimonials
- pretend to be a customer
- pretend a product is handmade/local if it is not
- fake scarcity or urgency
- hide material shipping fees
- hide return/refund conditions
- claim guaranteed results without evidence
- bypass CAPTCHAs, logins, paywalls, or access restrictions
- store raw secrets in logs or repo files
- make decisions from unverified assumptions without labels

## Approval record schema

```json
{
  "approval_id": "appr_001",
  "created_at": "2026-06-15T00:00:00Z",
  "requested_by": "marketmind_bot",
  "action": "launch_ad_test",
  "risk_level": "high",
  "status": "pending | approved | denied | expired | executed | failed",
  "summary": "Launch $50 test for Daily Driver Interior Kit",
  "expected_cost": 50,
  "max_cost": 50,
  "expected_revenue": 0,
  "expected_learning": "Test click and add-to-cart interest",
  "evidence_ids": [],
  "confidence": 0.71,
  "rollback_plan": "Pause campaign immediately and keep landing page live",
  "expires_at": "2026-06-17T00:00:00Z"
}
```

## Budget policy

V1 defaults:

```text
max_daily_ad_spend = 0 until explicitly set
max_per_niche_test = 0 until explicitly set
max_product_sample_order = 0 until explicitly set
max_paid_app_monthly_cost = 0 until explicitly set
```

No marketing spend is allowed until Aidan sets a budget.

## Escalation policy

Escalate to Aidan when:

- spend would exceed cap
- CAC exceeds break-even
- refund rate rises above threshold
- supplier quality is uncertain
- product evidence is weak
- customer complaint repeats
- platform account risk appears
- bot confidence is low but impact is high

## Daily approval summary

The bot should produce a daily approval queue:

```text
Pending approvals:
1. Launch $50 ad test for Product A — high risk — recommend approve
2. Publish revised landing page — medium/high — recommend approve
3. Increase budget to $25/day — high risk — recommend deny until CAC improves
```

## Expiration

Approvals should expire if not executed within the approved window.

Default: 48 hours.

## Audit log

Every approval action must log:

- who approved or denied
- timestamp
- action payload
- expected impact
- result
- P&L impact
- rollback status
