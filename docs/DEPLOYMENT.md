# Deployment

MarketMind has two deployable artifacts: the **backend API** (FastAPI) and the
**desktop app** (Tauri). The desktop app is a thin client of the API.

## Backend API (Docker)

The backend is packaged as a container (`Dockerfile` + `docker-compose.yml`).

```bash
# Build + run with Docker directly
docker build -t marketmind-api .
docker run -p 8000:8000 -v marketmind-data:/data marketmind-api

# …or with compose
docker compose up --build
```

- The API listens on `:8000`. Health check: `GET /health`.
- SQLite data persists in the `marketmind-data` volume (`/data` in the
  container). The app creates the schema on startup.
- **Auth:** set `MARKETMIND_API_TOKEN` to require `Authorization: Bearer <token>`
  on every request (health + docs stay open). Leave it unset only for trusted
  local networks. See `.env.example`.

```bash
MARKETMIND_API_TOKEN=$(openssl rand -hex 32) docker compose up --build
```

### Live integrations (optional, off by default)
The executor only performs live Stripe/Shopify calls when (a) the action is
APPROVED, (b) it is run with `dry_run=False`, and (c) the relevant credentials
are present: `STRIPE_API_KEY`, or `SHOPIFY_STORE_DOMAIN` + `SHOPIFY_ACCESS_TOKEN`.
Without them, live execution is refused (safe-fail). Never bake secrets into the
image — pass them at runtime.

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
5. Tag the release; attach the installer artifacts.
