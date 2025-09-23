# MASTER_DEV_PLAN_PROFIT_SAFE_HARDENED.md

⸻

## 0) Mission

Launch MarketMind with minimal risk, minimal profit drag, and maximum learning speed—while enforcing strict policy, margin, reliability, privacy and finance guardrails. Then scale only when KPIs are green.

⸻

## 1) Immutable Bot Laws (already in code, re-affirmed)

• Compliance > Revenue; block publish on red; auto-pause & build appeal pack.
• Profit floor (price ≥ landed_cost×(1+min_margin) incl. ship+fees).
• Respect MAP & parity; effective price (incl. coupons) ≥ MAP; Walmart parity check.
• Conservative undercut (cap step); 9-ending; free-ship math included.
• Shadow → Canary (1→5→25→100) with auto-rollback on KPI breach.
• Idempotency everywhere; circuit breakers; kill-switches.
• Explainability strings logged for every action.
• Finance guardrails: daily net ≥ $0; recon ≥ 99%; 14-day cash buffer intact.
• Privacy minimalism; PII redaction; reproducible models.

⸻

## 2) Optional Hardening — now mandatory in this plan

### 2.1 External Policy & Legal
• Marketplace counsel review of policy packs (MAP, parity, claims, category rules).
• Brand/MAP binder per brand: authorization letters, MAP schedule, contacts.
• Appeal templates pre-approved by counsel (suppression, IP claims, safety).

**DoD**: Signed memo from counsel + binder in S3 (object lock) + linter rules updated.

### 2.2 Security Red-Team & Hygiene
• Third-party pentest (app & cloud); fix all High/Critical.
• Hardware security keys (FIDO2) for all marketplace logins; 2FA enforced.
• Source/secret scanning (CI); key rotation (90–180d) automated.
• Network allowlisting for admin console/IPs; WAF on API.
• Honeytokens in S3; S3 Object-Lock (WORM) for journals & model cards.

**DoD**: Pentest report "no High/Critical outstanding", keys issued, allowlists live, object-lock verified.

### 2.3 Supplier Continuity
• 2–3 signed suppliers/SKU; neutral packing clause; SLA credits for late/defects.
• Quarterly failover drill; 3–5 days micro-stock at 3PL for top 20 SKUs.

**DoD**: Contracts in binder; drill runbook & pass report; micro-stock feed live.

### 2.4 Financial Resilience
• Profit/Tax/Reserve sub-accounts; sweep rules codified.
• Payout-hold simulation (e.g., 21 days) to ensure buffer sufficiency.
• Insurance (general + product liability); certificate stored.

**DoD**: Bank rules/screenshots; forecast shows ≥ buffer under "hold" scenario; policies uploaded.

### 2.5 Chaos & Disaster Recovery
• Monthly chaos: API 429/5xx storms, schema drift, supplier OOS spikes.
• Quarterly restore drill: RPO ≤ 15m, RTO ≤ 60m from encrypted backups/WAL.
• Error budgets: publish ≥ 99.5%, VTR ≥ 98%, ODR < 0.6%; auto feature freeze if breached.

**DoD**: Drill reports; freeze automation unit-tested; last-restore timestamp tile green.

### 2.6 Model Risk Controls
• PSI/KS drift monitors; shadow → canary → promote with uplift≥threshold & KPIs green.
• Model cards (data snapshot, metrics, constraints) stored with object-lock.
• Counterfactual eval (IPS/DR) before any live exploration to minimize profit drag.

**DoD**: Model registry entries complete; automated gate prevents promote without artifacts.

### 2.7 Operational Rehearsals
• Tabletops for: suppression/MAP dispute, carrier-code rejects, payout reserve.
• One-click kill-switch demoed end-to-end.

**DoD**: Minutes + evidence pack; kill-switch screencast & logs.

### 2.8 Observability Hard Stops
• Pager on: publish<99.5% (10m), VTR<98% (DoD), recon<99% (daily), cash<buffer (forecast).
• Incidents open with Suggested Fix and One-Click button.

**DoD**: Synthetic tests trigger and close automatically; playbooks verified.

### 2.9 Access Hygiene
• Least-privilege roles, quarterly access review, break-glass account offline.
• Session recording for admin actions; immutable audit logs.

**DoD**: Access review report; break-glass tested & sealed.

⸻

## 3) Learning Speed with Minimal Profit Drag

• Pre-train offline (12–24 months if available).
• Counterfactual replay of pricing & profit modules → drop changes with negative expected lift.
• Exploration budget tiny & targeted: pricing ε from 5% → 1% in 60 days; content A/B ≤ 5% traffic.
• Canary ramps on every change; auto-rollback on breach.
• Playbook Library auto-activates proven tactics for similar SKUs (with SIM + canary).

⸻

## 4) Profit Maximization (all safety-compliant)

**Revenue/CVR**: Smart bundles/kits (same DIM tier), MAP-safe coupons, variation consolidation, content A/B, offer framing, daypart/seasonality micro-adjusts (±1%).

**Margin/Cost**: Supplier re-bid (≥2 quotes/SKU) + early-pay 2%/10 (buffer≥2×), defect/late chargebacks, fee-aware categorization, long-tail pruning (bottom 10–20% by 30-day net).

**Shipping/CX**: Carrier map optimizer + auto-repost tracking, micro-stock for top 20 SKUs (3–5 days), WISMR scripts (instant credit ≤$10), proactive ETA + $2 goodwill.

**Expected lift**: +10–15% monthly net from Month 3 onward (conservative), with all guardrails unchanged.

⸻

## 5) Config (hardened defaults)

```yaml
guardrails:
  min_net_margin_pct: 15
  respect_map: true
  max_undercut_step_pct: 3
  psychological_pricing: "9-ending"
  free_shipping: true
  price_publish_success_target_pct: 99.5
  valid_tracking_target_pct: 98
  odr_max_pct: 0.6
  daily_net_guardrail_usd: 0
  reconciliation_target_pct: 99
  cash_buffer_min_usd: 2000         # ↑ buffer for hardening
  canary_ramp_steps: [1,5,25,100]
  model_uplift_min_pct: 4

learning.pricing:
  algo: "linucb_ts"
  explore_rate_start_pct: 5
  explore_rate_floor_pct: 1
  constraints:
    min_net_margin_pct: 15
    respect_map: true
    max_undercut_step_pct: 3
    psychological_pricing: "9-ending"
    free_shipping_included: true
  daypart: { enabled: true, max_adjust_pct: 1 }

marketing:
  tacos_cap_pct: 8
  sp_roas_floor: 3.0
  walmart_roas_floor: 3.0
  stop_loss: { roas_floor_days: 2, tacos_cap_days: 3 }
  ab_testing: { traffic_cap_pct: 5, min_cvr_uplift_pp: 0.3 }

growth_governor:
  prune_bottom_pct: 10
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
  rollback_triggers: { consecutive_red_days: 2 }

security:
  2fa_hardware_keys: true
  ip_allowlist_admin: true
  s3_object_lock: true
  key_rotation_days: 120

drills:
  chaos_monthly: true
  restore_quarterly: { rpo_minutes: 15, rto_minutes: 60 }
  error_budget_freeze: true
```

⸻

## 6) Timeline (who does what, when)

### T-60 to T-45 (Policy/Sec kickoff)
• **Legal**: policy pack review; brand/MAP binders.
• **SecOps**: pentest SOW; key issuance; IP allowlists; S3 object-lock.
• **Eng**: finish adapters, guardrails API; journaling to S3.
• **Finance**: open sub-accounts; sweep rules.

**Exit**: Counsel memo, security baseline live.

### T-44 to T-30 (Foundation complete)
• **Supplier**: 2–3 contracts/SKU; neutral packing clause; micro-stock plan.
• **Eng**: reconciliation ≥99% on historical; chaos harness ready.
• **Ops**: 3PL hookup; returns/WISMR scripts.
• **Marketing**: SEO polish & coupon/bundle configs staged.

**Exit**: Supplier continuity verified; recon backtests ≥99%.

### T-29 to T-14 (Hardening & training)
• **SecOps**: pentest executed; fixes merged (no High/Critical).
• **Eng/ML**: offline pre-train; counterfactual replays; model cards.
• **Finance**: payout-hold simulation; buffer confirmed.

**Exit**: Pentest closed; model registry & cards complete.

### T-13 to T-7 (Shadow Week)
• Full mirror run (no publish); chaos drills (429, schema, OOS); MTTR API ≤3m; schema ≤10m.
• DR restore drill; RPO/RTO within targets.

**Exit**: Shadow pass; DR pass; incidents 0.

### T-6 to T-2 (Freeze & canary prep)
• Freeze guardrails; kill-switch walkthrough; carrier map & auto-repost verified.
• Marketing canary budgets set; A/B traffic cap = 5%.

**Exit**: Freeze note; canary plan approved.

### T-0 to T+7 (Launch & ramp)
• Publish 1% canary; monitor tiles hourly; step to 5%/25%/100% only if gates hold (publish≥99.5%, VTR≥98%, ODR<0.6%, daily net≥0, recon≥99%).
• Auto-rollback on breach; incident with one-click fix.

**Exit**: Full rollout; post-mortem & evidence pack to S3.

### T+8 to T+30 (Stabilize & learn)
• ε → 3% then → 1%; promote winners; prune bottom 10%; supplier re-bid round 1.
• Finance: first sweep proposal; tax/reserve funded.

**Exit**: Green for 14 days; Growth Governor allows first expansion (+2 sub-niches or +10–15% SKUs).

⸻

## 7) Testing & Acceptance (must pass to ship)

• **Unit/Contract tests**: adapters, idempotency, guardrails, ledger property tests.
• **Backtests**: pricing vs baseline (floors/MAP enforced); profit modules IPS/DR; demand MAPE; risk PR/AUC.
• **Shadow Week**: full E2E mirror; chaos MTTRs within SLO.
• **Perf**: API p95 ≤ 250 ms; order E2E p95 ≤ 60 s @ 10×.
• **Recon backtest**: ≥ 99% over 60 days.
• **Security**: pentest "clean"; 0 critical CVEs; hardware keys live; IP allowlists on.
• **DR**: restore drill success logged ≤ 60 m.

⸻

## 8) Marketing OS (unchanged safety; canary budgets)

• Amazon/eBay/Walmart marketplace-first with ROAS/TACoS guards and stop-loss.
• Auto term mining → exact/phrase scaling; negatives weekly.
• Coupons/bundles before list cuts; fast-tag only when on-time prob ≥ 95%.

⸻

## 9) Finance & Profit Collection

• Settlement ingest → double-entry → ≥99% recon → cash forecast.
• Weekly sweep ONLY if: buffer ok, daily net ≥0 (7d), recon ≥99%, VTR ≥98%, ODR <0.6%.
• Split example: 50% Reinvest / 20% Tax / 10% Reserve / 20% Owner.

⸻

## 10) Go/No-Go & Freeze/Unfreeze

**Go if** (7 consecutive days):
Publish ≥ 99.5%, VTR ≥ 98%, ODR < 0.6%, recon ≥ 99%, daily net ≥ $0, cash forecast ≥ buffer, last DR < 90d, last chaos < 30d.

**Auto-freeze**: On error-budget breach (any KPI red beyond budget). Unfreeze after 48h green + postmortem merged.

⸻

## 11) Expected Economics (unchanged guardrails)

• **Safe path**: Month-12 net ≈ $5.88k/mo.
• **With profit modules**: Month-12 ≈ $6.59k/mo (+12% from M3).
• **Accelerated (theoretical)** from Month 6: +$3.5k cumulative uplift M6–M12; ops +$40/mo.

(These are directional; no guarantees. Gates & rollbacks minimize downside.)

⸻

## 12) Owner's Weekly Routine (10–15 min)

• Check tiles: publish, VTR/ODR, recon, cash runway, ROAS/TACoS, Profit Uplift.
• Click: Approve SIM winners, Promote Terms, Add Negatives, Acknowledge Sweep (if green).
• If any red, the bot already paused/rolled back; you'll see one-click fix.

⸻

## Final word

This is the tightest, most conservative, fastest-learning route we can take: heavy hardening, tiny but targeted exploration, rigorous SIM/backtests, strict canaries, and profit levers that never weaken safety. If it isn't green, it won't scale; if it twitches, it rolls back—and tells you why.
