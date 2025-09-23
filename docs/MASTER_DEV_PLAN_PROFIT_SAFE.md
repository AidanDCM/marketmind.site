# MASTER_DEV_PLAN_PROFIT_SAFE.md

⸻

## 0) Mission & Non-Negotiables

**Mission**: Launch a multi-niche, self-healing marketplace system that maximizes profit subject to strict policy, reliability, and margin guardrails. Scale only when KPIs are green.

**Bot Laws (always on)**:
1. Compliance > Revenue (MAP/parity/restricted terms; auto-pause + appeal packs)
2. Profit floor preserved: price ≥ landed_cost × (1+min_margin) (incl. ship+fees)
3. Conservative undercut (cap step; psychological 9-ending; free-ship math)
4. Canary gating 1→5→25→100 with auto-rollback on KPI breach
5. Explainability strings for every action (inputs + guardrails)
6. Idempotency; circuit breakers; token rotation; S3 journaling
7. Kill-switches (global/per-channel) halt publishing, not fulfillment
8. Privacy minimalism & DSR; reproducible models (feature hashes)
9. Finance guardrails: daily net ≥ 0; 14-day cash buffer; recon ≥ 99%

⸻

## 1) System Architecture

• **API**: FastAPI (apps/hive_api)
  - Routers: health, governance/rules, listings, learning, finance, marketing, profit
• **Workers**: Celery (apps/hive_worker)
  - Queues: ingest, pricing, publish, compliance, settlements, reconciliation, learning, marketing, profit_ops
• **Shared libs**: packages/shared
  - config, db, models, adapters, guardrails, finance, learning, profit_boosters, explanations
• **Stores**: Postgres (OLTP), S3 (journaling/artifacts), Redis (queues/cache)
• **Console**: Next.js (apps/console) — tiles + controls + approvals
• **Observability**: JSON logs + metrics; Google Sheets echo

⸻

## 2) Repo Layout (canonical)

```
apps/
  hive_api/
    routers/{health,governance,learning,listings,finance,marketing,profit}.py
  hive_worker/
    tasks/{ingest,pricing,publish,compliance,settlements,reconciliation,
           learn_pricing,learn_content,learn_supplier,marketing,
           supplier_rebid,bundle_builder,content_ab,carrier_optimizer,
           profit_orchestrator}.py
packages/
  shared/
    config.py
    db/{engine.py,session.py}
    models/{core.py,finance.py,experiments.py,profit.py}
    adapters/{base.py,amazon.py,ebay.py,walmart.py,cj.py,autods.py,keepa.py}
    guardrails.py
    finance/{ledger.py,forecast.py}
    learning/{bandits.py,experiments.py,feature_store.py}
    profit_boosters/{bundles.py,coupons.py,variation.py,fees.py,pruning.py}
    shipping/{carrier_map.py,micro_stock.py}
    cx/{wismr.py,proactive_eta.py}
    marketing/{keywords.py,ads.py,roas_tacos.py}
    explanations.py
apps/console/app/pages/{overview,pricing,learning,marketing,finance,profit,incidents}.tsx
infra/docker/{docker-compose.yml, *Dockerfiles}
docs/{MASTER_DEV_PLAN_PROFIT_SAFE.md}
```

⸻

## 3) Config (drop-in)

```yaml
guardrails:
  min_net_margin_pct: 15
  respect_map: true
  max_undercut_step_pct: 3
  psychological_pricing: "9-ending"
  free_shipping: true
  valid_tracking_target_pct: 98
  price_publish_success_target_pct: 99.5
  daily_net_guardrail_usd: 0
  reconciliation_target_pct: 99
  cash_buffer_min_usd: 1500
  canary_ramp_steps: [1,5,25,100]
  model_uplift_min_pct: 4

growth_governor:
  gates:
    price_publish_success_pct_min: 99.5
    valid_tracking_rate_pct_min: 98.0
    order_defect_rate_pct_max: 0.6
    daily_net_usd_min_days: 14
    reconciliation_pct_min: 99
    supplier_failover_success_pct_min: 98
    api_quota_headroom_pct_min: 25
    sku_efficiency_net_usd_per_sku_min_30d: 8
    cohort_gmv_to_portfolio_median_min: 0.6
  add_step_options:
    - { type: "subniches", count: 2, skus_per_subniche: [10,20] }
    - { type: "skus_percent", percent: 15 }
  rollback_triggers:
    consecutive_red_days: 2
  prune_bottom_pct: 10

learning:
  pricing:
    algo: "linucb_ts"
    explore_rate_start_pct: 5
    explore_rate_floor_pct: 1
    min_net_lift_pct_to_promote: 4
    constraints:
      min_net_margin_pct: 15
      respect_map: true
      max_undercut_step_pct: 3
      psychological_pricing: "9-ending"
      free_shipping_included: true
    daypart: { enabled: true, max_adjust_pct: 1 }
  content:
    max_traffic_under_test_pct: 5
    min_cvr_uplift_pp_to_promote: 0.3
  supplier_routing:
    sla_on_time_prob_min: 0.95
    oos_penalty: 2.0
  rollout:
    canary_steps_pct: [1,5,25,100]
    rollback_on_breach: true
  gates:
    vtr_min_pct: 98.0
    price_publish_success_min_pct: 99.5
    odr_max_pct: 0.6
    daily_net_min_usd: 0
    reconciliation_min_pct: 99
    cash_buffer_min_usd: 1500

bundles: { enabled: true, same_tier_only: true, max_units: 3 }
pricing:
  use_coupons: true
  offer_framing_preferred: true
  max_undercut_step_pct_by_bucket: { inelastic: 1, neutral: 2, elastic: 3 }
supplier_bids: { enabled: true, min_bidders: 2 }
early_pay: { enabled: true, min_cash_buffer_multiplier: 2.0 }
shipping: { auto_repost_tracking: true }
cx: { instant_credit_threshold_usd: 10, proactive_eta: true, goodwill_credit_usd: 2 }

marketing:
  tacos_cap_pct: 8
  sp_roas_floor: 3.0
  walmart_roas_floor: 3.0
  ebay_promoted_std_pct: "2-4"
  budget: { daily_per_niche_usd: "15-50", monthly_per_niche_usd: "300-800" }
  stop_loss: { roas_floor_days: 2, tacos_cap_days: 3 }
  ab_testing: { traffic_cap_pct: 5, min_cvr_uplift_pp: 0.3 }
  bids: { min_cpc_usd: 0.15, max_cpc_usd: 1.20 }
  promos: { prefer_coupons: true, bundle_builder_enabled: true }
```

⸻

## 4) Integrations & Use

• **Amazon SP-API / eBay / Walmart**: offers/prices, orders, settlements, performance → ingest, price, publish, reconcile
• **Suppliers (CJ, AutoDS)**: catalog, cost, stock, lead time → supplier routing + redundancy
• **(Optional) Keepa**: Amazon price/BSR signals for research features
• **Google Sheets (SA)**: ledgers, KPI snapshots, experiments, incidents, compliance echoes
• **AWS S3**: raw req/resp journaling, appeal packs, artifacts

Adapters live in `packages/shared/adapters/*` with contract tests, rate limits, retries, and circuit breakers.

⸻

## 5) Data Model (core)

• products, listings, offers, competitor_offers
• suppliers, supplier_offers, routes
• price_history, price_events
• orders, order_items, returns, ship_scans
• fees, payouts, settlements, ledger_entries (double-entry)
• experiments, variants, assignments, metrics
• incidents, policy_events
• feature_store_* views (point-in-time)
• profit_modules_log (each profit action + reason + guardrail checks)

⸻

## 6) Brains & Tasks

**Ingest** → normalize → upsert → write price_history
**Pricing** → floor (COGS+ship+fees+min margin), MAP/parity, competitor context → proposed price
**Publish** → idempotent updates + circuit breakers
**Compliance** → pre-publish linter (terms/images/category/MAP) & post-publish suppression handler (auto-pause + appeal pack)
**Learning** → constrained bandits (pricing), Bayesian A/B (content), supplier routing policy
**Marketing** → term mining ↔ negatives, ROAS/TACoS stop-loss, coupon/bundle ops
**Finance** → settlements ingest, reconciliation ≥99%, cash forecast, sweep proposals
**Profit Orchestrator** → coordinates boosters below, with guards

⸻

## 7) Profit Maximization (safety-compliant)

### 7.1 Revenue/CVR boosters
1. **Smart Bundles/Kits** (2/3-packs, same DIM tier)
   • Worker: bundle_builder.py (SIM → linter → canary)
   • Safety: MAP honored; floor recompute includes ship/fees
   • Expected: +6–10% net on affected SKUs

2. **MAP-safe Coupons / Offer Framing**
   • Worker: profit_orchestrator.py (coupons)
   • Safety: "effective price ≥ MAP" check before publish
   • Expected: +2–5% net via CVR lift

3. **Variation Consolidation** (merge under parent)
   • Worker: variation.py (policy-aware attributes)
   • Safety: category rules enforced by linter
   • Expected: +3–6% net

4. **Content A/B** (titles/bullets/images)
   • Worker: content_ab.py (≤5% traffic)
   • Safety: pre-publish compliance linter; no price tests first 60 days
   • Expected: +0.3–0.6 pp CVR → +3–7% net

5. **Daypart/Seasonality Micro-Adjusts** (±1%)
   • Module: pricing.daypart with SIM first
   • Safety: floors & MAP honored
   • Expected: +1–2% net

### 7.2 Margin/Cost boosters
6. **Supplier Re-bid** (≥2 quotes/SKU monthly) + Early-Pay 2%/10 when buffer ≥2×
   • Workers: supplier_rebid.py; finance buffer guard pre-checked
   • Expected: COGS −2–5% → +5–10% net on those SKUs

7. **Defect/Late Chargebacks** (auto-file with evidence)
   • Module: supplier_claims
   • Expected: +0.5–1.5% portfolio net

8. **Fee-Aware Categorization**
   • Module: fees.py optimizer (valid subs only)
   • Expected: +0.5–1% net

9. **Long-Tail Pruning** (pause bottom 10–20% by 30-day net)
   • Module: pruning.py (re-qualify via SIM later)
   • Expected: +3–5% portfolio net

### 7.3 Shipping/CX protectors (indirect profit)
10. **Carrier Map Optimizer + Auto-Repost Tracking**
    • Worker: carrier_optimizer.py
    • Safety KPI: keep VTR ≥ 98%
    • Expected: fines avoided; +1–2% net saved

11. **3PL Micro-Stock for Top ~20 SKUs** (3–5 days)
    • Module: shipping/micro_stock.py (dropship fallback remains)
    • Expected: +2–4% net on those SKUs

12. **WISMR CX Micro-Scripts** (instant credit ≤$10; partial refund; fast reship)
    • Module: cx/wismr.py
    • Safety KPI: ODR < 0.6%
    • Expected: lower returns/ODR costs

13. **Proactive ETA + $2 Goodwill Credits**
    • Module: cx/proactive_eta.py
    • Expected: ratings ↑, returns ↓ → +1–2% net

**Blended uplift** (conservative, non-overlapping): ~+10–15% monthly net from Month 3 onward without loosening any guardrails.

⸻

## 8) Marketing OS (policy-safe, marketplace-first)

• **Amazon**: SEO polish; SP Auto → term mining → Manual exact/phrase; coupons; bundles; ROAS/TACoS guards
• **eBay**: Promoted Listings Standard 2–4%; item specifics; variation parents
• **Walmart**: LQS≥90; Sponsored Products exact; fast tags only when on-time prob≥95%
• **Spend Governor**: TACoS cap (≤8%); ROAS floors (3.0); stop-loss (48–72h); budgets scale only when core KPIs pass gates

⸻

## 9) Observability & Sheets Echo

• **Dashboard tiles**: publish success, VTR/ODR, error rates, queue depth, MTTR, reconciliation %, cash runway, ROAS/TACoS, Profit Uplift (by module)
• **Sheets tabs**: KPI_Snapshot, Orders, Payouts, COGS, Supplier_Payables, Ledger, Recon_Mismatches, Compliance_Violations, Pricing_Decisions, Experiments, Incidents, Model_History, Feature_Drift, Profit_Modules_Log
• Rolling monthly; S3 backlog; protected headers

⸻

## 10) Finance & Collecting Profits

• Ingest settlements → double-entry ledger → ≥99% reconciliation → cash forecast
• Weekly Sweep Proposal (only when: buffer ok, daily net ≥0 (7d), recon ≥99%, VTR ≥98%, ODR <0.6%)
• Split (example): 50% Reinvest / 20% Tax / 10% Reserve / 20% Owner (console-configurable)

⸻

## 11) Testing & Backtesting (must pass)

**Unit/Contract**: adapters, guardrails, idempotency, ledger property tests
**SIM/Backtests**:
• Pricing vs baseline (floors/MAP enforced)
• Profit modules (bundles/coupons/daypart) counterfactual replay with IPS/DR
• Demand forecasting MAPE; risk PR/AUC (FN capped)
**Shadow Week** (T-7): full mirror; chaos drills (429 storm, schema drift, OOS) → MTTR ≤ 3–10 min
**Perf**: API p95 ≤ 250 ms; order E2E p95 ≤ 60 s @ 10× load
**Recon backtest**: ≥ 99% over 60 days
**Security**: 0 critical CVEs; PII redaction verified

⸻

## 12) Perfect Launch (T-30 → T-0 → T+7)

**T-30→T-14**: approvals/keys, 2–3 suppliers/SKU, policy packs, finance wiring, insurance
**T-7**: Shadow week; chaos drills; perf + recon pass
**T-48h**: freeze guardrails; carrier map; kill-switch test
**T-0→T+7**: canary ramp 1→5→25→100 only if daily gates hold: publish≥99.5%, VTR≥98%, ODR<0.6%, daily net≥0. Rollback on breach.

⸻

## 13) Growth Plan (safe + accelerated)

Baseline costs: setup ≈ $1,450; monthly ops ≈ $355; safety float (not spent) $3,250.

**Safest 12-month ramp** (add only if last-30-day gates green):

| Mo | Niches | Sub-niches | SKUs | Net / mo |
|----|--------|------------|------|----------|
| 1  | 3      | 9          | 120  | −$5      |
| 2  | 4      | 12         | 220  | $655     |
| 3  | 5      | 15–20      | 300  | $1,260   |
| 4  | 6      | 18–24      | 380  | $1,810   |
| 5  | 7      | 21–28      | 460  | $2,470   |
| 6  | 8      | 24–32      | 540  | $3,130   |
| 7  | 9      | 27–36      | 620  | $3,680   |
| 8  | 10     | 30–40      | 700  | $4,120   |
| 9  | 10     | 32–42      | 780  | $4,560   |
| 10 | 11     | 36–44      | 860  | $5,000   |
| 11 | 12     | 42–48      | 940  | $5,440   |
| 12 | 12     | 48         | 1,050| $5,880   |

**Safe profit add-ons** (+12% from M3, ops unchanged):
M3 $1,411, M4 $2,027, M5 $2,766, M6 $3,506, M7 $4,122, M8 $4,614, M9 $5,107, M10 $5,600, M11 $6,093, M12 $6,586 (≈ +$4.98k cumulative vs baseline).

**Theoretical limit** (accelerated from M6, ops +$40/mo, +12% scale uplift):
M6 +$335, M7 +$402, M8 +$454, M9 +$507, M10 +$560, M11 +$613, M12 +$666 vs safe → +$3,537 uplift (M6–M12).

**Growth Governor** (enforced): add only if all gates green (section 3). If red for 2 days → freeze & prune bottom 10–20%.

⸻

## 14) Incident Playbooks (auto → your 1-click)

• **API 429/5xx** → backoff/shrink/open circuit → Resume conservative
• **Schema drift** → shadow adapter → Promote fix/Rollback
• **Supplier OOS/late** → failover/pause → Approve alternate
• **Carrier reject** → update map + re-post → Confirm & close
• **MAP/parity red** → block publish + compliant price → Publish compliant
• **Suppression** → auto-pause + appeal pack → Submit appeal
• **Margin erosion** → reduce undercut, revert price → Lock floor 7d
• **Cash squeeze** → halt expansion → Freeze non-core SKUs
• **Model drift** → rollback; schedule retrain → Promote after shadow
• **DB/queue** → quiesce writers; replay → Resume writers
• **Secret anomaly** → rotate/revoke → Confirm & audit

⸻

## 15) Sprints (developer checklist)

**S1 — Foundations**: health, config, DB+Alembic, adapters (CJ, SP-API/eBay/Walmart sandbox), ingestion, price_history, guardrails API, Sheets echo, S3 journaling

**S2 — Pricing & Compliance**: floor/MAP/parity, undercut cap, 9-ending, linter, suppression handler, publisher + circuits, canary toggles

**S3 — Finance & Recon**: settlements ingest, double-entry ledger, recon ≥99%, forecast, sweeps API & tile

**S4 — Learning v1**: bandits (pricing) with constraints, content A/B, feature store, model registry, explanations

**S5 — Marketing OS**: keyword mining, negatives, ROAS/TACoS guardrails, coupons/bundles ops, per-niche budgets, tiles

**S6 — Profit Modules**: supplier_rebid, early_pay guards, bundle_builder, variation merge, fee optimizer, pruning, carrier optimizer, micro_stock, WISMR, proactive_eta

**S7 — Safety & DR**: self-repair runbooks, kill-switches, backups+WAL, DR drill, chaos drills (429, schema, OOS) with MTTR measures

**S8 — Shadow & Launch**: shadow harness, canary ramp manager, rollback path, operator buttons

⸻

## 16) Ops Cadence

**Weekly** (10–15 min): close incidents → 0 red compliance → approve SIM winners → recon mismatches <1% → review Profit Uplift module logs

**Monthly** (45–60 min): supplier scorecards, publish policy pack diffs, cash forecast ≥ buffer, promote canary model (uplift ≥ threshold)

**Quarterly** (60–90 min): key rotation, DR restore drill (RPO≤15m/RTO≤60m), chaos triad (API drift + OOS + carrier reject)

⸻

## 17) Success Probabilities (with all safeguards)

• **Pessimistic**: 40–50%
• **Conservative**: 70–80%
• **Base**: 80–90%
• **Optimistic**: 92–97%

(We don't claim 99%+ due to irreducible external risks; gates/rollbacks keep exposure small.)

⸻

## "Done" Gate (ship only if all green)

• Publish ≥ 99.5%, VTR ≥ 98%, ODR < 0.6%
• Recon ≥ 99% (60-day backtest)
• API p95 ≤ 250 ms; E2E order p95 ≤ 60 s @ 10×
• 0 critical CVEs; PII redaction verified
• Shadow week passed; canary rollback verified
• Cash forecast ≥ buffer; daily net guardrail satisfied

⸻

This plan gives your devs exactly what to build, in what order, with the profit engines turned on — and every decision still locked behind policy, margin, and reliability guardrails.
