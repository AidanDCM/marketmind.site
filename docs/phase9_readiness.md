# Phase 9 Readiness Checklist

This document captures the final verification steps, dependencies, and migrations required before starting Phase 9.

## Status Summary (Phase 8)
- Pydantic v2 migration: COMPLETE
- FastAPI lifespan migration: COMPLETE
- Audit persistence (DB + optional Sheets): COMPLETE
- Phase 8 tests and E2E: PASS locally
- Integrations verification (`make verify-integrations`): PASS
- Secrets hygiene docs updated: IN PROGRESS (scrub `.env` defaults)
- Load test sanity: PASS (USERS=100 SPAWN=10 DURATION=60), 0 failures; archive: `docs/reports/load-20250821-124223.tgz`

## Open Items Prior to Phase 9
- Secrets hygiene
  - [x] Review local `.env` for default/weak placeholders; rotate to strong values
  - [x] Ensure `.env.example` only contains safe placeholders
  - [x] Run `make security-check` and resolve findings
- External API live smoke tests
  - [x] Set `FLAG_SIMULATION_ENABLED=false` with real API keys
  - [x] Validate CJ and Google Sheets minimal live calls — PASS
  - [ ] Amazon SP-API minimal call — PENDING (refresh token not yet provided)
  - [x] Document results in `docs/phase8_test_report.md` with artifacts
- SQLAlchemy 2.0 model updates
  - [x] Migrate `Product` model to 2.0 annotations `Mapped[]` + `mapped_column()`
  - [x] Verify relationships and model registrations

## Execution Plan (Recommended Sequence)
1. Security and secrets
   - Run `make security-check` (gitleaks + pip-audit + npm audit)
   - Address any secrets scan and dependency CVEs
2. API health and regression
   - Start API: `make api-local`
   - Verify: `make verify-integrations`
3. Audit persistence
   - Ensure tables exist: `make audit-db`
   - Smoke insert: Python one-liner to `log_config_change()` and confirm row exists
4. External smoke (live)
   - Export real creds, set `FLAG_SIMULATION_ENABLED=false`
   - Hit minimal endpoints for CJ/Sheets (done) and Amazon (pending refresh token)
5. Load sanity (COMPLETED)
   - Ran: `USERS=100 SPAWN=10 DURATION=60 make load-test-report`
   - Result: 0 failures; Archive: `docs/reports/load-20250821-124223.tgz`
6. Phase 9 kickoff
   - Complete Product model migration to SQLAlchemy 2.0
   - Draft migration notes and update alembic if needed

## Acceptance Criteria for Phase 9 Start
- [ ] All local tests green: `make test`, `make phase8-tests-nocov`, `make phase8-e2e`, `make adapters-health`
- [ ] Verify integrations 100% pass
- [ ] Secrets scan clean and dependency audit acceptable
- [ ] Live smoke tests completed for CJ & Sheets; Amazon either completed or explicitly waived with rationale
- [ ] Audit DB persistence validated end-to-end
- [ ] Documentation updated (runbooks, changelog, test reports)

### Important (Credentials Follow-Up)
- Amazon SP-API requires keys and refresh token setup after the fact. Until provided, Amazon-affecting flows remain in simulation and are excluded from live smoke. See `docs/credentials_followup.md` for retrieval steps and verification commands.

## Artifacts to Produce
- Updated README and CHANGELOG with Phase 8 finalization summary
- Test artifacts: `reports/load/*` (if load test executed)
- Docs: updated `docs/secrets_runbook.md`, this checklist, and a brief Phase 8 report summarizing results
