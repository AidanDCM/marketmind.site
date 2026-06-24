# Audits & Analyses — MarketMind standard

Every recurring operator analysis ships as a **triad**. A number without a
runbook is a rumor; a runbook without a saved report is a promise.

## The triad (all three required for new audits)

1. **Tool** — `scripts/<name>.py` + testable logic in `marketmind/` (pure functions, unit-tested).
2. **Runbook** — `docs/audits/<NAME>_RUNBOOK.md` (preconditions, commands, fields, ordered interpretation, failure modes).
3. **Report** — committed artifact under `reports/<name>/`, one file per run, header references the runbook.

## Authoring checklist

- [ ] Logic in `marketmind/<module>.py` + tests in `tests/test_<module>.py`
- [ ] CLI writes report file by default
- [ ] Runbook with § preconditions, commands, field definitions, interpretation rules
- [ ] Registry row below
- [ ] `docs/engineering_log/YYYY-MM-DD-<slug>.md` entry

## Registry

| Analysis | Tool | Runbook | Reports dir | Notes |
|---|---|---|---|---|
| Deploy verification | `scripts/verify_marketmind_deploy.py` | (inline docstring + `docs/DEPLOYMENT.md`) | — | CI job runs against local API |
| Operator readiness | `scripts/check_operator_readiness.py` | `OWNER_MANUAL.md` § operator | — | `--api` for live check |
| QA final audit | — | `docs/qa/final_audit.md` | `docs/qa/` | Point-in-time |

**Future triads** (experiment scorecard, daily operator audit) must follow the full
three-leg pattern before production reliance.

## One-off audits

`docs/qa/final_audit.md` and `docs/issues/*` are point-in-time evidence. They
follow the spirit: methodology, commands, conclusions — not summaries.
