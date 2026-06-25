# Deployment

MarketMind has two deployable artifacts: the **backend API** (FastAPI) and the
**desktop app** (Tauri). The desktop app is a thin client of the API.

## Backend API (Docker)

The backend is packaged as a container (`Dockerfile` + `docker-compose.yml`).

```bash
# Build + run with Docker directly
docker build -t marketmind-api .
docker run -p 8000:8000 -v marketmind-data:/data -v marketmind-logs:/app/logs marketmind-api

# …or with compose
docker compose up --build
```

The compose stack runs two services:
- **`api`** — FastAPI on `:8000`
- **`scheduler`** — nightly `marketmind-scheduler` (default 06:00 local); waits for API health

```bash
# API only (no scheduler)
docker compose up --build api
```

- The API listens on `:8000`. Health check: `GET /health`.
- SQLite data persists in the `marketmind-data` volume (`/data` in the
  container). The app creates the schema on startup via Alembic.
- Operator logs (`operator_events.jsonl`, `mistakes.jsonl`) persist in the
  `marketmind-logs` volume mounted at `/app/logs`.
- **Auth:** set `MARKETMIND_API_TOKEN` to require `Authorization: Bearer <token>`
  on every request (health + docs stay open). Leave it unset only for trusted
  local networks. See `.env.example`.

```bash
MARKETMIND_API_TOKEN=$(openssl rand -hex 32) docker compose up --build
```

### Checklist thresholds (optional)

Override scale-readiness gates without code changes:

| Variable | Default | Purpose |
|---|---|---|
| `MARKETMIND_CHECKLIST_MIN_VISITS` | 100 | Min qualified visits before scale |
| `MARKETMIND_CHECKLIST_MIN_ORDERS` | 5 | Min orders before scale |
| `MARKETMIND_CHECKLIST_MIN_SPEND` | 50.0 | Min ad spend ($) before scale |

Inspect active values: `GET /operator/checklist-config`.

### Scripted deploy (Windows)

```powershell
.\scripts\deploy_marketmind.ps1
.\scripts\deploy_marketmind.ps1 -ApiToken "your-long-random-token"
```

The script builds, starts `docker compose`, and polls `/health` for up to 60s.

### Post-deploy verification

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/operator/preflight
curl http://127.0.0.1:8000/operator/health-panel
curl http://127.0.0.1:8000/operator/readiness
curl http://127.0.0.1:8000/operator/integrations
curl http://127.0.0.1:8000/operator/checklist-config
```

Or run the bundled verifiers after deploy (API must be reachable):

```bash
python scripts/verify_marketmind_deploy.py
python scripts/check_operator_readiness.py --api
```

`verify_marketmind_deploy.py` hits `/health`, `/operator/health-panel`,
`/operator/readiness`, and `/operator/integrations`. The integrations check fails if
the JSON body contains forbidden secret substrings (`sk_test_`, `sk_live_`, `shpat_`,
`whsec_`, `Bearer `) — configured integrations must stay metadata-only.

Both verifiers run in CI and in `python scripts/local_ci.py --full`.

Healthy: `health.status == "ok"`. Review `preflight.blockers` before any live
execution. If `MARKETMIND_API_TOKEN` is set, add
`-H "Authorization: Bearer <token>"` to every call except `/health`.

CI runs the same verifier against a temporary uvicorn instance on every push/PR
(see `.github/workflows/ci.yml`, job `deploy-verify`).

### Rollback

```powershell
.\scripts\rollback_marketmind.ps1          # stop container, keep volumes
.\scripts\rollback_marketmind.ps1 -RemoveVolumes   # destructive — wipes DB + logs
```

**Code rollback** (after stopping or alongside a volume-preserving stop):

```bash
git log --oneline -10
git checkout <last-good-sha> -- .
python -m pytest -q
.\scripts\deploy_marketmind.ps1
```

**Data backup** before destructive rollback:

```bash
docker run --rm -v marketmind-site_marketmind-data:/data -v %CD%:/backup alpine \
  tar czf /backup/marketmind-data-backup.tgz -C /data .
```

Volume names may differ — run `docker volume ls | findstr marketmind` first.

See `docs/issues/0002-deploy-rollback-runbook.md` for the full operator runbook.

### Live integrations (optional, off by default)
The executor only performs live Stripe/Shopify calls when (a) the action is
APPROVED, (b) it is run with `dry_run=False`, and (c) the relevant credentials
are present: `STRIPE_API_KEY`, or `SHOPIFY_STORE_DOMAIN` + `SHOPIFY_ACCESS_TOKEN`.
Without them, live execution is refused (safe-fail). Never bake secrets into the
image — pass them at runtime. The API defaults `dry_run=True` when omitted.

## Desktop app (Tauri installer)

```bash
cd desktop
npm ci
npm run tauri build
```

Outputs (Windows) under `desktop/src-tauri/target/release/bundle/`:
- `nsis/MarketMind Autopilot_<version>_x64-setup.exe` (NSIS installer)
- `msi/MarketMind Autopilot_<version>_x64_en-US.msi` (MSI)

The unpackaged binary is at `desktop/src-tauri/target/release/marketmind-desktop.exe`.
macOS/Linux produce `.dmg`/`.AppImage`/`.deb` respectively when built on those
platforms (`bundle.targets` is `all`).

### Pointing the desktop app at a remote API
The client targets `http://127.0.0.1:8000` by default (`desktop/src/api/client.ts`,
`BASE`). To use a remote backend, change `BASE` and rebuild, and store the API
token in `localStorage` under `marketmind_api_token` so requests are
authenticated. (The window CSP in `tauri.conf.json` must also allow the remote
origin in `connect-src`.)

## Release checklist
1. `python -m pytest -q` and `python -m ruff check .` green.
2. `cd desktop && npm test && npm run build` green.
3. Bump `version` in `pyproject.toml` and `desktop/src-tauri/tauri.conf.json`.
4. Build the backend image and the desktop installer.
5. Run `.\scripts\deploy_marketmind.ps1` (or VPS equivalent) and verify health.
6. Tag the release; attach the installer artifacts.
