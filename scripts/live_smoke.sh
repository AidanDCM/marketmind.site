#!/usr/bin/env bash
set -euo pipefail

# Live external API smoke tests for MarketMind
# Requires: FLAG_SIMULATION_ENABLED=false and real credentials exported
# Writes outputs to reports/smoke/ and prints a concise summary

API_BASE="http://127.0.0.1:8001"
OUT_DIR="reports/smoke"
TIMEOUT=20

mkdir -p "$OUT_DIR"

# Optionally load environment from common .env locations (names only echoed later)
maybe_source_env() {
  set +u
  local candidates=(
    ".env"
    "infra/.env"
    "secrets/.env"
    "config/.env"
    "$HOME/.env"
    "$HOME/.config/marketmind/.env"
    "$HOME/Library/Application Support/MarketMind/.env"
  )
  for f in "${candidates[@]}"; do
    if [ -f "$f" ]; then
      # shellcheck disable=SC1090
      set -a; source "$f"; set +a
      echo "[INFO] Loaded environment from $f" >&2
      break
    fi
  done
  set -u
}

maybe_source_env

info()  { echo "[INFO] $*"; }
success(){ echo "[PASS] $*"; }
warn()  { echo "[WARN] $*"; }
fail()  { echo "[FAIL] $*"; }

# Check SIMULATION flag
SIM=${FLAG_SIMULATION_ENABLED:-true}
if [ "${SIM}" != "false" ]; then
  warn "FLAG_SIMULATION_ENABLED is not false. Set FLAG_SIMULATION_ENABLED=false for true live calls."
fi

overall_pass=0

echo "=== Live Smoke Tests (external APIs) ==="

# Print detection summary (names only)
echo "[INFO] Environment detection (names only):"
for v in \
  AMAZON_SP_API_CLIENT_ID AMAZON_SP_API_CLIENT_SECRET AMAZON_SP_API_REFRESH_TOKEN \
  AMAZON_SP_API_ROLE_ARN AMAZON_SP_API_LWA_APP_ID AMAZON_SP_API_LWA_CLIENT_SECRET \
  CJ_API_KEY GOOGLE_APPLICATION_CREDENTIALS; do
  if [ -z "${!v-}" ]; then echo "  - $v=<unset>"; else echo "  - $v=<set>"; fi
done

# 1) Amazon SP-API minimal pricing snapshot (single ASIN)
info "Amazon SP-API smoke: pricing snapshot"
if [ -z "${AMAZON_SP_API_CLIENT_ID:-}" ] || [ -z "${AMAZON_SP_API_CLIENT_SECRET:-}" ] || \
   [ -z "${AMAZON_SP_API_REFRESH_TOKEN:-}" ] || [ -z "${AMAZON_SP_API_ROLE_ARN:-}" ]; then
  warn "Amazon SP-API credentials not fully set; skipping Amazon smoke."
else
  if resp=$(curl -sS --max-time $TIMEOUT -X POST "$API_BASE/ingest/run/pricing" \
      -H 'Content-Type: application/json' \
      -d '{"asins":["B08N5WRWNW"],"write_to_sheets":false}'); then
    echo "$resp" > "$OUT_DIR/amazon_pricing.json"
    success "Amazon pricing snapshot request returned 200 (see $OUT_DIR/amazon_pricing.json)" || true
    overall_pass=$((overall_pass+1))
  else
    fail "Amazon pricing snapshot request failed"
  fi
fi

# 2) CJ catalog page 1
info "CJ API smoke: catalog sync"
if [ -z "${CJ_API_KEY:-}" ]; then
  warn "CJ_API_KEY not set; skipping CJ smoke."
else
  if resp=$(curl -sS --max-time $TIMEOUT -X POST "$API_BASE/ingest/run/catalog" \
      -H 'Content-Type: application/json' \
      -d '{"supplier":"cj"}'); then
    echo "$resp" > "$OUT_DIR/cj_catalog.json"
    success "CJ catalog request returned 200 (see $OUT_DIR/cj_catalog.json)" || true
    overall_pass=$((overall_pass+1))
  else
    fail "CJ catalog request failed"
  fi
fi

# 3) Google Sheets optional audit append via pricing write_to_sheets
info "Google Sheets smoke (optional): pricing snapshot with write_to_sheets=true"
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
  warn "GOOGLE_APPLICATION_CREDENTIALS not set; skipping Sheets smoke."
else
  if resp=$(curl -sS --max-time $TIMEOUT -X POST "$API_BASE/ingest/run/pricing" \
      -H 'Content-Type: application/json' \
      -d '{"asins":["B08N5WRWNW"],"write_to_sheets":true}'); then
    echo "$resp" > "$OUT_DIR/sheets_pricing.json"
    success "Pricing with write_to_sheets returned 200 (see $OUT_DIR/sheets_pricing.json)" || true
    overall_pass=$((overall_pass+1))
  else
    fail "Sheets pricing snapshot request failed"
  fi
fi

echo "=== Summary ==="
if [ $overall_pass -gt 0 ]; then
  success "Completed $overall_pass live smoke(s). Check $OUT_DIR for artifacts."
else
  warn "No live smokes executed (missing creds or SIMULATION not disabled)."
fi
