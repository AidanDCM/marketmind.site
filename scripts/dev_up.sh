#!/usr/bin/env bash
set -euo pipefail

# MarketMind dev bootstrap: build, up, health check, and open the console
# Usage: ./scripts/dev_up.sh [--no-build]

NO_BUILD=false
if [[ "${1:-}" == "--no-build" ]]; then
  NO_BUILD=true
fi

# Resolve repo root (script may be invoked from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Choose compose command (Docker Compose v2 preferred)
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
  COMPOSE=(docker compose)
elif command -v docker-compose &>/dev/null; then
  COMPOSE=(docker-compose)
else
  echo "[dev_up] ERROR: Docker Compose not found. Install Docker Desktop." >&2
  exit 1
fi

COMPOSE_FILE="docker-compose.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
  # fallback to dev override
  if [[ -f "docker-compose.dev.yml" ]]; then
    COMPOSE+=(-f docker-compose.dev.yml)
  else
    echo "[dev_up] ERROR: No docker-compose.yml present in $REPO_ROOT" >&2
    exit 1
  fi
fi

# Optional build
if [[ "$NO_BUILD" == false ]]; then
  echo "[dev_up] Building images…"
  "${COMPOSE[@]}" build --pull
else
  echo "[dev_up] Skipping build (--no-build)"
fi

# Up services in background
echo "[dev_up] Starting services…"
"${COMPOSE[@]}" up -d

# Print status
"${COMPOSE[@]}" ps

# Health checks
API_URL=${NEXT_PUBLIC_API_URL:-"http://127.0.0.1:8001"}
CONSOLE_URL=${NEXT_PUBLIC_CONSOLE_URL:-"http://127.0.0.1:3000"}

HEALTH_ENDPOINT="$API_URL/health/summary"

echo "[dev_up] Waiting for API healthy at $HEALTH_ENDPOINT …"
ATTEMPTS=60
SLEEP=2
ok=false
for ((i=1; i<=ATTEMPTS; i++)); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" || true)
  if [[ "$code" == "200" ]]; then
    ok=true
    break
  fi
  sleep "$SLEEP"
  if (( i % 5 == 0 )); then echo "  still waiting… ($i)"; fi
done

if [[ "$ok" != true ]]; then
  echo "[dev_up] WARNING: API not healthy after $((ATTEMPTS*SLEEP))s. Check logs: ${COMPOSE[*]} logs -f api" >&2
else
  echo "[dev_up] API is healthy."
fi

# Open browser (macOS) to console onboarding
if command -v open &>/dev/null; then
  echo "[dev_up] Opening console: $CONSOLE_URL/onboarding"
  open "$CONSOLE_URL/onboarding" || true
else
  echo "[dev_up] Console available at: $CONSOLE_URL/onboarding"
fi

cat <<'EOF'

Next steps:
  1) Check container logs if needed:
       docker compose logs -f api console worker
  2) From the Console, run the Onboarding flow (Seed → Connect → Simulate → Approve)
  3) Visit Pricing to approve proposals or try Approve All

Tips:
  - Re-run without rebuild: ./scripts/dev_up.sh --no-build
  - Tear down:           docker compose down -v
  - API health:          curl -sS http://127.0.0.1:8001/health/summary | jq .

EOF
