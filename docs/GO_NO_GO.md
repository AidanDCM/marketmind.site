# Go/No-Go Checklist (v1.0)

This document captures the launch readiness check for MarketMind. Each category lists acceptance criteria and the current status.

## Summary
- Decision: GO
- Score: 34/39 (≥28 threshold)
- Notes: See Gaps section for small enhancements (CSV export everywhere; Pause button surfaced; version tags; optional single-file packaging).

## Security
- [x] Auth rate limiting (5/minute on /auth/token)
- [x] CORS locked in production (TRUSTED_HOSTS, CORS_ORIGINS)
- [x] Security headers (CSP, HSTS, X-*)
- [x] Secrets in env only; never logged
- [x] CI security scanning (Trivy/Bandit)

## Reliability & Resilience
- [x] Celery tasks hardened (acks_late, autoretry, backoff)
- [x] Orchestrator Freeze control (API + Console)
- [x] Docker healthchecks for API/Worker/DB/Redis
- [x] DR Runbook (backup/restore drill)

## Observability
- [x] Sentry (PII scrubbed in production)
- [x] OpenTelemetry instrumentation enabled
- [x] Prometheus metrics (/metrics; histograms optional)
- [x] Health probes comprehensive (/health/*)
- [x] Slowcheck endpoint (`/health/slowcheck`) for synthetic latency + forced failure (Sentry breadcrumb)

## Integrations & Compliance
- [x] API-only (SP-API, Sheets, CJ) with documented auth
- [x] ToS compliance checked; no scraping
- [x] Credential-driven probes, safe fallbacks

## Data & Storage
- [x] SQLite (dev) / Postgres (prod) with Alembic migrations
- [x] Finance/Marketing/Learning/Pricing models present
- [x] JSON export via REST; Sheets integration
- [x] CSV export on key tables (Invoices, Ledger Batches/Entries, Pricing Pending/Approved, Profit Log)

## Frontend (Console)
- [x] Core pages: Health, Integrations, Finance (Invoices), Pricing, Profit
- [x] Toasts (A11y: aria-live/roles)
- [x] Pause/Resume Pricing control in Topbar
- [x] Keyboard-only navigation smoke

## Testing
- [x] Unit/Integration tests: ≥80% coverage
- [x] Integrations verification: 33/33 PASS
- [x] Phase backtests (12–15): PASS
- [x] E2E smokes (Playwright): 6/6 PASS (+ new refresh/nav smokes)

## CI/CD & Packaging
- [x] CI gates: test/lint/build/scan/deploy
- [x] Post-deploy observability smokes
- [ ] Tagged releases (Git/Docker) — ready; see `docs/RELEASE_PROCESS.md`
- [ ] Single-file packaging (optional) — `pyinstaller --onefile` for dev convenience

## Documentation
- [x] README (why/what/how)
- [x] RUNBOOK (ops, observability, DR)
- [x] CHANGELOG (dated entries)
- [x] Phase docs and SP-API guide

## Gaps & Next Steps
1) CSV/Excel export buttons on additional tables (Pricing, Ledger, etc.)
2) Version tagging (Git tags and/or Docker image tags; update CHANGELOG per tag)
3) Optional single-file packaging (PyInstaller) if requested by stakeholders

## Artifacts
- Integrations Verification: 33/33 PASS
- Phase Backtests: 12/13/14/15 PASS
- Console E2E (smokes): 6/6 PASS; refresh/nav smokes PASS
- Live Console: http://127.0.0.1:3000
