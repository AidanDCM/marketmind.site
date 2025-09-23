# Phase 9 Approval & Final Readiness Gate (2025-08-21 22:15 ET)

Owner: MarketMind Engineering
Scope: Approvals, waivers, mitigation, and execution plan to achieve flawless integration and operation before Phase 10

## Executive Summary
- Readiness to start governance implementation: GREEN
- All local quality gates pass; load sanity PASS; CJ & Google Sheets live smokes PASS.
- Single external dependency blocker: Amazon SP-API refresh token not available yet; cannot execute minimal live smoke.
- Approval granted to begin Phase 9 with a time-boxed waiver for Amazon live smoke, with strict mitigation and tracking.
 - Credentials follow-up (Critical): see `docs/credentials_followup.md` for all required keys/IDs and retrieval steps. Phase 9 continues excluding Amazon live smoke until credentials are provided.

## Approvals
- Policy & Risk Engines (observe-only) — APPROVED
- Arbitrator (SIMULATION) — APPROVED
- Contract Monitor (page-only) — APPROVED
- Self-Repair (low-risk runbooks) — APPROVED
- Release/Canary Manager (cohort 1%) — APPROVED (guarded)
- Secret/Config Rotator — APPROVED
- Compliance Watcher — APPROVED
- Chaos Lab (staging-only) — APPROVED

## Pending Item and Best Option
- Amazon SP-API Live Smoke
  - Status: PENDING (missing `AMAZON_SP_API_REFRESH_TOKEN`)
  - Best Option: Time-boxed waiver with controls
    - Duration: 5 business days or until token received
    - Mitigation:
      - Keep `FLAG_SIMULATION_ENABLED=true` for any Amazon-affecting endpoints in production-like tests
      - Enable Contract Monitor for Amazon endpoints to detect schema drift while waiting
      - Require `assert-pricing-checkpoint` only when `configured==true` (already implemented in `Makefile`)
      - Proceed with CJ/Sheets live flows to validate cross-service pipelines end-to-end
    - Exit Criteria:
      - Provide refresh token and re-run live smoke runner: `scripts/live_smoke.sh`
      - Attach sanitized JSON artifacts under `reports/smoke/`

## Test & Backtest Matrix (to be executed per phase checkpoint)
- Unit: policy evaluator truth tables, risk scoring bands, arbitrator precedence
- Contract: golden schemas per adapter; drift triggers page-only alert
- Integration: pricing publish under policy gates; orders KPIs SLOs
- Chaos (staging): worker kill, 429/5xx, latency; verify auto-repair + SLO recovery
- Backtests: 30-day replay pricing/orders/tax deltas within tolerance
- Security: gitleaks + pip-audit; rotation reload; log redaction

## Commands (authoritative)
```bash
# Health & integrations
make api-local            # terminal 1
make verify-integrations  # terminal 2

# Phase 8/7 asserts
make phase8-e2e
USERS=100 SPAWN=10 DURATION=60 make load-test-report
make archive-load-report

# Live smoke (CJ/Sheets; Amazon when token is ready)
export FLAG_SIMULATION_ENABLED=false
chmod +x scripts/live_smoke.sh && ./scripts/live_smoke.sh

# Governance scaffolding (next steps)
make migrate-up  # ensure DB at head before adding new migrations
```

## Documentation Links
- Governance Playbook: `docs/phase9_governance.md`
- Readiness Checklist: `docs/phase9_readiness.md`
- Phase 8 Report: `docs/phase8_test_report.md`

## Sign-offs
- Engineering: APPROVED
- QA: APPROVED (with Amazon waiver controls)
- Security: APPROVED
- Product: APPROVED

## Waiver Record
- Item: Amazon SP-API live smoke
- Reason: Missing refresh token
- Controls: Simulation on for Amazon, contract monitor enabled, no production side effects
- Expiration: 5 business days from this document date or upon token receipt (whichever sooner)
- Remeasure: Re-run `scripts/live_smoke.sh` and attach artifacts
