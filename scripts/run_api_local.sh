#!/usr/bin/env bash
set -euo pipefail
# Local (no Docker) API run helper
# Requires: Python 3.12+, pip, virtualenv (optional)

# Load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Default to SQLite for local if DB_URL not set
export DB_URL="${DB_URL:-sqlite:///./dev.db}"
export APP_ENV="${APP_ENV:-dev}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

python -m uvicorn apps.hive_api.main:app --reload --host 127.0.0.1 --port 8000
