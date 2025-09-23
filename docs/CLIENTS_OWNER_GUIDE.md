# MarketMind Client Owner's Guide (Local, Single-Team)

This guide helps your team get MarketMind running locally with a single shared console (no accounts required) and a smooth onboarding path.

## Prerequisites
- Docker Desktop 4.x (or Docker Engine + Compose v2)
- Node.js 18+ and pnpm or npm (only needed if running the console without Docker)
- Python 3.9+ (only needed if running the API without Docker)

## Quick Start (Recommended: Docker Compose)

1. Copy console environment file:
   ```bash
   cp apps/console/.env.local.example apps/console/.env.local
   ```
   Adjust `NEXT_PUBLIC_API_URL` if your API is not on `http://127.0.0.1:8001`.

2. Start all services:
   ```bash
   docker compose -f docker-compose.dev.yml up -d --build
   ```

3. Open the console:
   - Console: http://127.0.0.1:3000
   - API: http://127.0.0.1:8001/_info (for a quick sanity check)

4. Onboarding flow:
   - Go to `/onboarding` and click “Seed Demo Data”, or set `NEXT_PUBLIC_AUTO_SEED=true` in `apps/console/.env.local` to seed automatically on first load.
   - Connect Integrations (optional for local) — the Integrations page shows configuration status using `/health/data`.
   - Run a simulation to generate pricing proposals.
   - Approve & push (eBay dry-run) from the Pricing page.

## Auth-Free Local Mode
For a single local team, we disable login across the console:
- In `apps/console/.env.local`:
  ```
  NEXT_PUBLIC_AUTH_DISABLED=true
  NEXT_PUBLIC_ONBOARDING_PUBLIC=true
  ```
- The console will not require login and will not send Authorization headers.
- IMPORTANT: This is for local use only. For production, remove these flags and re-enable auth.

## Running Without Docker (optional)

API:
```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -r requirements.txt

# Run API (FastAPI/Uvicorn behind Gunicorn in production; Uvicorn OK for dev)
uvicorn apps.hive_api.main:app --reload --port 8001
```

Console (Next.js):
```bash
cd apps/console
cp .env.local.example .env.local
pnpm install   # or npm install
pnpm dev       # or npm run dev
# Open http://127.0.0.1:3000
```

## Environment Variables (Console)
- `NEXT_PUBLIC_API_URL`: API base URL (default `http://127.0.0.1:8001`)
- `NEXT_PUBLIC_AUTH_DISABLED`: `true` to bypass console login (local only)
- `NEXT_PUBLIC_ONBOARDING_PUBLIC`: `true` to allow public onboarding route
- `NEXT_PUBLIC_AUTO_SEED`: `true` to auto-seed demo data on first load

## Environment Variables (API)
- See `packages/shared/config` and `.env.production.example` for a full list.
- For local dev, sensible defaults are used; Redis is optional (rate-limiting gracefully falls back in dev).

## Health & Troubleshooting
- API health: `GET /health/summary`, `GET /health/data`
- Integrations health: `GET /health/integrations`
- Logs: `docker compose logs -f api` and `docker compose logs -f console`
- Common issues:
  - CORS: Ensure console `NEXT_PUBLIC_API_URL` matches your API URL.
  - Auth: In local mode, console skips tokens; for production, unset `NEXT_PUBLIC_AUTH_DISABLED`.
  - DB: The dev compose includes Postgres; if you run API without compose, ensure database is configured.

## What’s Included
- Onboarding Wizard (Seed → Connect → Simulate → Approve)
- Integrations page with status and recent calls
- Pricing Lab to simulate, approve, and push (eBay dry-run) with export actions
- Console 404 and error pages
- Privacy and Terms pages (link to repo root authoritative docs)

## Production Notes
- For production, enable auth and RBAC, configure secrets, and set secure CORS:
  - Remove `NEXT_PUBLIC_AUTH_DISABLED` and set trusted `CORS_ORIGINS` in API settings.
  - Follow `docker-compose.prod.yml` and CI/CD guidance.
  - Observe the CSP/security headers enforced in `apps/console/app/layout.tsx` and API middleware.

If you need help, open `/integrations` to verify connectivity, check `/health/data`, and consult the logs. This guide is designed to get your team fully running locally with minimal friction.
