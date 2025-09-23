# Issues Log

Continuously updated log of blockers, bugs, and resolutions. Keep this in sync with development events.

## Open
- [2025-08-11] Docker Engine unreachable from CLI
  - Symptom: `Cannot connect to the Docker daemon` for contexts `desktop-linux` and `default`.
  - Impact: Cannot build or start the compose stack.
  - Suspected Cause: Docker Desktop Engine not fully started or socket/context mismatch.
  - Next Steps: Restart Docker Desktop, confirm “Engine running” in UI; verify `docker info`; retry compose.
- [2025-08-11] Local shell startup error (.bash_profile)
  - Symptom: `/Users/aidanmiller/.bash_profile: unexpected EOF` breaks commands when using login shells.
  - Impact: `curl` and other commands fail when executed via `bash -l`.
  - Mitigation: Run processes via non-login shells (`bash -c`), avoid sourcing `.bash_profile` for local scripts, or fix `.bash_profile` syntax.

## Resolved
- [2025-08-11] Local API running with SQLite
  - Details: Uvicorn on `127.0.0.1:8001`; `/health/data` returns DB OK.
- [2025-08-11] Local ingestion stub successful
  - Details: `scripts/run_ingest_local.py` wrote sample rows to `dev.db` (multiple runs).
- [2025-08-11] Redis not running in local no-Docker mode
  - Details: Redis is now running locally and reachable at `redis:6379`.
- [2025-08-11] Redis available locally and health green
  - Details: `redis-cli PING` -> `PONG`; API started on `127.0.0.1:8002` with `REDIS_URL=redis://127.0.0.1:6379/0`; `/health/data` reports Redis OK.
  - Details: `scripts/run_ingest_local.py` wrote sample rows to `dev.db` (multiple runs).
 - [2025-08-11] Redis available locally and health green
   - Details: `redis-cli PING` -> `PONG`; API started on `127.0.0.1:8002` with `REDIS_URL=redis://127.0.0.1:6379/0`; `/health/data` reports Redis OK.
   - Details: `scripts/run_ingest_local.py` wrote sample rows to `dev.db` (multiple runs).
