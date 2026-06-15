# MarketMind Autopilot P&L Model

## Purpose

This document defines the money rules for MarketMind. The bot must understand profit before it recommends store launches, ads, supplier orders, or scale actions.

## Core formula

```text
revenue
- product cost
- packaging cost
- shipping cost
- platform fees
- payment processing fees
- return/refund/damage allowance
- ad spend
- software/tool allocation
= contribution profit
```

## Key terms

### AOV

Average order value.

### Gross profit before ads

```text
AOV - product cost - packaging - shipping - fees - refund allowance
```

### Break-even CAC

The maximum customer acquisition cost before the first order becomes unprofitable.

```text
break_even_cac = gross_profit_before_ads
```

### Safe CAC

A lower target CAC that leaves profit and protects against reporting error.

```text
safe_cac = break_even_cac * 0.50 to 0.70
```

### Contribution profit

```text
gross_profit_before_ads - CAC
```

## Product test input schema

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

## Product test output schema

```json
{
  "gross_profit_before_ads": 26.0,
  "break_even_cac": 26.0,
  "safe_cac_low": 13.0,
  "safe_cac_high": 18.2,
  "estimated_contribution_profit": 12.0,
  "margin_status": "healthy",
  "recommended_action": "test",
  "risks": []
}
```

## Example scenarios

## Scenario 1: healthy paid-test product

```text
Sale price: $59
Product cost: $18
Packaging: $1.50
Shipping: $8
Fees: $3.50
Refund allowance: $2
Software allocation: $0.50
Gross profit before ads: $25.50
Estimated CAC: $14
Contribution profit: $11.50
```

Recommendation: controlled paid test allowed if budget is approved.

## Scenario 2: product cannot support ads

```text
Sale price: $39
Product cost: $16
Packaging: $1.50
Shipping: $9
Fees: $2.50
Refund allowance: $2
Software allocation: $0.50
Gross profit before ads: $7.50
Estimated CAC: $18
Contribution profit: -$10.50
```

Recommendation: do not run paid ads. Fix AOV, bundle, pricing, shipping, or kill.

## Scenario 3: heavy product trap

```text
Sale price: $49
Product cost: $12
Packaging: $2
Shipping: $22
Fees: $3
Refund allowance: $3
Software allocation: $0.50
Gross profit before ads: $6.50
Estimated CAC: $10
Contribution profit: -$3.50
```

Recommendation: reject unless shipping can be reduced or AOV increased.

## Kill rules

Kill or pause when:

- CAC is above break-even for 3 consecutive days
- contribution profit is negative after meaningful traffic
- 500 qualified visits produce zero sales
- add-to-cart rate is below 3 percent after qualified traffic
- checkout start is healthy but purchase rate is weak, indicating price/shipping/trust issue
- refund or defect rate rises above 8-10 percent
- shipping cost exceeds planned estimate by more than 20 percent
- supplier quality evidence is weak or inconsistent

## Scale rules

Only recommend scaling when:

- contribution profit is positive
- CAC is below safe CAC target
- conversion rate is stable
- refund/complaint rate is acceptable
- shipping and fulfillment are reliable
- enough orders exist to reduce false signal risk
- ad account/platform risk is low

## Budget rules

V1 defaults:

```text
initial_allowed_spend = $0
max_ad_spend_without_manual_approval = $0
max_test_budget_without_manual_approval = $0
max_sample_order_without_manual_approval = $0
```

Aidan must explicitly set budgets before spending begins.

Suggested first serious test:

```text
samples: $50-$200
landing page/tools: $0-$50
initial ad test: $50-$150
serious ad test: $300-$750 only after early signal
```

## Daily report metrics

Every daily report should show:

- revenue
- order count
- AOV
- product cost
- shipping cost
- refund allowance
- ad spend
- CAC
- gross profit before ads
- contribution profit
- conversion rate
- add-to-cart rate
- checkout-start rate
- refund rate
- recommended action

## Recommended actions

The P&L model should emit one of:

```text
reject
revise_offer
organic_only_test
paid_test_requires_approval
continue_test
pause_ads
kill_product
scale_requires_approval
```

## Operating principle

A store that sells but loses money is not a win. MarketMind must optimize for profitable learning first, profitable scaling second, and revenue vanity last.
