#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8001}"
CURL="curl -sS"

pass() { echo -e "\033[32m✔\033[0m $1"; }
fail() { echo -e "\033[31m✘\033[0m $1"; exit 1; }
info() { echo -e "\033[34mℹ\033[0m $1"; }

info "Using API_BASE=${API_BASE}"

# Wait for API readiness (/_info), up to ~15s locally
READY=0
for i in {1..30}; do
  if ${CURL} "${API_BASE}/_info" >/dev/null 2>&1; then READY=1; break; fi
  sleep 0.5
done
if [ "$READY" != "1" ]; then
  info "API not reachable at ${API_BASE}. Skipping observability smoke (local optional)."
  exit 0
fi

info "1) Hitting /health/integrations to prime health checks..."
$CURL "${API_BASE}/health/integrations" >/dev/null || fail "health/integrations not responding"

info "2) Rechecking a few times to populate Prometheus histograms..."
for i in {1..3}; do
  $CURL "${API_BASE}/health/integrations" >/dev/null || fail "health/integrations failed on attempt $i"
  sleep 0.5
done
pass "Health integrations endpoint OK"

info "3) Simulating slow check (Sentry breadcrumb, if enabled)"
SLOW_JSON=$($CURL "${API_BASE}/health/slowcheck?ms=600" || true)
echo "$SLOW_JSON" | jq . >/dev/null 2>&1 || true
pass "Slowcheck (ms=600) responded"

info "4) Simulating forced failure (should return HTTP 500, but not fail the script)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_BASE}/health/slowcheck?ms=200&fail=true" || true)
if [[ "$HTTP_CODE" == "500" ]]; then
  pass "Slowcheck forced failure returned 500 as expected"
else
  info "Slowcheck forced failure returned ${HTTP_CODE} (non-500)."
fi

if $CURL "${API_BASE}/metrics" >/dev/null 2>&1; then
  info "5) Inspecting /metrics for health_check_latency_ms..."
  METRICS=$($CURL "${API_BASE}/metrics" | grep -E "^health_check_latency_ms" || true)
  if [[ -n "$METRICS" ]]; then
    echo "$METRICS" | head -n 15
    pass "Prometheus histogram health_check_latency_ms found"
  else
    info "No health_check_latency_ms found (prometheus_client may be missing or histogram disabled)."
  fi
else
  info "/metrics not mounted (prometheus_client may be unavailable)."
fi

info "6) Optional: Check a summarized health view"
$CURL "${API_BASE}/health/summary" | jq . >/dev/null 2>&1 && pass "Health summary OK" || info "Summary endpoint not available or jq missing"

info "7) OTel check (best validated in your APM backend)." 
info "   Ensure OTEL_RESOURCE_ATTRIBUTES/OTEL_EXPORTER_OTLP_ENDPOINT are set in production."

pass "Observability smoke complete"
