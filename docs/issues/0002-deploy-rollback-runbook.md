# Issue 0002: Deploy and rollback runbook

## Symptom

Operator needs a repeatable way to deploy the MarketMind API to Docker and roll
back safely when a release misbehaves.

## Context

Deployment docs existed (`docs/DEPLOYMENT.md`) but lacked scripted verification,
volume backup instructions, and a dated issue record. OWNER_MANUAL handoff
checklist items for deploy/rollback were unchecked.

## Root cause

Slice-by-slice development prioritized features over operator deploy tooling.

## Working solution

1. **`scripts/deploy_marketmind.ps1`** — builds compose stack, starts detached,
   polls `GET /health` for 60s, prints preflight URL.
2. **`scripts/rollback_marketmind.ps1`** — `docker compose down`, optional volume
   removal, prints git + backup checklist.
3. **`docker-compose.yml`** — healthcheck, `marketmind-logs` volume for append-only
   JSONL files, checklist threshold env passthrough.
4. **`docs/DEPLOYMENT.md`** — post-deploy curls, rollback, backup commands.

## Files changed

- `scripts/deploy_marketmind.ps1`
- `scripts/rollback_marketmind.ps1`
- `docker-compose.yml`
- `docs/DEPLOYMENT.md`
- `OWNER_MANUAL.md`
- `docs/issues/0002-deploy-rollback-runbook.md` (this file)

## Tests added or updated

- `tests/test_api.py::test_execute_defaults_to_dry_run` — API never live-executes
  when `dry_run` is omitted from the request body.

## Reusable lesson

Every deployable service needs: (1) a script that verifies health after start,
(2) a rollback script that preserves data by default, and (3) an issue log entry
so the next operator does not rediscover the procedure.

## Date

2026-06-23
