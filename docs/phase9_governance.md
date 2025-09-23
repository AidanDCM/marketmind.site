# Phase 9 — Governance, Longevity & Recursive Intelligence

This playbook defines the governance layer for MarketMind.

Objectives
- Self-governing: policy-driven, audit-ready, kill-switchable
- Self-repairing: detect → diagnose → act → verify → rollback
- Future-proof: auto-adapt to API/schema/version changes
- Accountable: tamper-evident logs, reproducible decisions, KPIs/SLOs
- Ethical & compliant: marketplace ToS, MAP, taxes, data protection

Current status (2025-08-22)
- Policy Engine: observe-only implemented (`packages/services/governance/policy_engine.py`), loads YAML rules from `config/governance/policies.yaml` and writes to `governance_decision`.
- Risk Engine: observe-only implemented (`packages/services/governance/risk_engine.py`), ingests signals with banding and writes to `risk_event`.
- Arbitrator: SIMULATION mode implemented (`packages/services/governance/arbitrator.py`), records simulated choices to `governance_decision`.
- Contract Monitor: page-only implemented (`packages/services/governance/contract_monitor.py`), detects schema drift, writes `risk_event`.
- Reports: CSV exports + summary implemented (`packages/services/governance/reports.py`).
- Dashboards/Sheets echoes: implemented (`packages/services/governance/dashboards.py`) using `packages/shared/sheets.py`.
- Tests added under `tests/services/` for Policy, Risk, Arbitrator, Contract Monitor, Reports, and Dashboards.
- Quick backtest target added: `make phase9-backtest` (migrate → governance tests → adapters health).

New services (overview)
- Policy Engine: declarative rules, precedence, allow/deny
- Risk Engine: scoring, banding, recommended actions
- Arbitrator: multi-brain conflict resolution under policy
- Self-Repair Controller: runbooks + verify/rollback
- Contract Monitor: API/schema drift detection and contract tests
- Release/Canary Manager: progressive rollout with guards
- Secret/Config Rotator: rotation cadence + zero-downtime reload
- Compliance Watcher: MAP, restricted terms, ToS/tax deltas
- Chaos Lab: controlled fault injection and resilience validation

Data model (tables)
- policy_rule(id, version, scope, kind, expr, effect, priority, enabled, created_at)
- governance_decision(id, ts, actor, subject, input, outcome, policy_ids[], risk_before, risk_after, notes)
- risk_event(id, ts, source, signal, score, level, correlated_incident_id?) [partitioned]
- incident(id, opened_at, closed_at?, title, severity, status, root_cause, remediation, evidence_uri)
- dependency_catalog(id, kind, name, current_version, target_version, status, last_checked_at)
- api_contract(id, provider, endpoint, version, schema_hash, last_green_at, drift_since?)
- release_rollout(id, artifact, version, cohort, started_at, aborted_at?, metrics_snapshot, status)
- chaos_experiment(id, name, scope, blast_radius, hypothesis, started_at, ended_at, result)
- kpi_threshold/slo_budget(metric, window, target, burn_rate_alert_thresholds)
- model_registry(id, name, version, hash, eval_score, deployed_at, retired_at?)
- security_finding(id, ts, source, severity, description, status, fix_commit?)

Policy rule skeleton (YAML)
```yaml
- id: map-price-floor
  scope: {channel: "amazon"}
  kind: pricing
  priority: 10
  effect: deny
  expr:
    any:
      - lt: [ proposed_price_cents, map_cents ]
      - lt: [ net_margin_pct, min_margin_pct ]
```

Evaluator sketch (Python)
```python
def evaluate_policies(policies, ctx):
    hits = []
    for r in sorted(policies, key=lambda r: r['priority']):
        if eval_rule(r, ctx):
            hits.append(r)
            if r['effect'] == 'deny':
                return {'allowed': False, 'hits': hits}
    return {'allowed': True, 'hits': hits}
```

Arbitrator sketch
```python
def arbitrate(decisions, context):
    policy = evaluate_policies(load_policies(context), context)
    if not policy['allowed']:
        return {"allowed": False, "reason": "policy_deny", "hits": policy['hits']}
    scored = [(d, weight(d.brain)*d.confidence) for d in decisions if d.allowed]
    best = max(scored, key=lambda x: x[1])[0] if scored else None
    return {"allowed": bool(best), "chosen": best, "notes": {"hits": policy['hits']}}
```

Runbooks (self-repair examples)
- Restart worker deployment; verify health
- Reduce batch sizes; increase backoff on 429/5xx
- Enable shadow adapter on schema drift; run contract suite; canary
- Rotate credentials on 401 storm; re-probe; toggle SIMULATION if needed

Dashboards & Sheets echoes

- Sheets client: `packages/shared/sheets.py` (`SheetsClient`, `LedgerWriter`).
- Governance exporter: `packages/services/governance/dashboards.py`.
- Programmatic usage:
  ```python
  from sqlalchemy.orm import Session
  from packages.services.governance.dashboards import export_to_sheets

  def push(session: Session):
      res = export_to_sheets(session, org_id="org1")
      # res = {configured: bool, tabs: {tab_name: {...}}, summary: {...}}
  ```
- Tabs written (idempotent by id): "Governance Decisions", "Risk Events", "Incidents", "Rollouts".
- If Sheets is not configured (e.g., CI): exporter returns `{configured: False, error: "not_configured"}` gracefully.

Reports exports

- CSV paths via `packages/services/governance/reports.py::export_csv(session, org_id, out_dir)`.
- Summary via `summarize(session, org_id)` returning counts of decisions, risk events, incidents, and active rollouts.

Testing matrix
- Unit: evaluator truth table, arbitrator precedence, risk scoring, reports export, dashboards exporter (not-configured path)
- Contract: golden schemas per adapter; drift → fallback path (Contract Monitor raises `risk_event`)
- Integration: price publish under policy gates; orders SLA guards
- Chaos: worker kill, latency, 429/5xx; verify SLO recovery
- Backtests: quick governance backtest `make phase9-backtest` green locally; 30-day replay TBD
- Security: log redaction, rotation reload, SBOM/CVE scan

Rollout plan
1) Observe-only Policy/Risk Engines
2) Arbitrator in SIMULATION (log only)
3) Self-Repair for low-risk runbooks
4) Contract Monitor (page-only)
5) Canary policy enforcement (1% → 100%)
6) Full release manager and kill-switch controls

Developer checklist
- Migrations (tables, indexes, partitions)
- Policy Engine + seed rules + hot-reload
- Risk Engine signals ingestion
- Arbitrator API + decision ledger
- Self-Repair + verify/rollback hooks
- Contract Monitor + schema hash + shadow seam
- Release/Canary cohort metrics + abort rules
- Secret/Config rotation + audit
- Compliance Watcher wiring
- Chaos Lab (staging; flagged in prod)
- Dashboard governance view + Sheets echoes

Migrations status
- Alembic revision `9f1a2b3c4d5e` created: Phase 9 governance schema.
- Tables added: `policy_rule`, `governance_decision`, `risk_event`, `incident`, `api_contract`, `release_rollout`, `chaos_experiment`, `kpi_threshold`, `slo_budget`, `security_finding`.
- Indices on org/time/entity keys; `risk_event` fields structured to be partition-ready.

Acceptance Criteria
- End-to-end tests: unit, contract, integration, chaos, and backtests pass
- Dashboard governance view shows policy hits, risk events, incidents, rollouts, SLOs
- Runbooks and alerts live; error budgets enforced
