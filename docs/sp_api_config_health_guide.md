# SP-API Configuration & Health Guide

This guide explains how MarketMind enables integrations based on credentials, how to configure Amazon/eBay/Walmart/CJ/Sheets/S3, and how to read the API health endpoints and Prometheus metrics.

## Credential-Driven Enablement

Integrations are automatically enabled when valid credentials are present. If credentials are missing, the integration is treated as "not configured" and does not raise an error in health checks.

- Amazon SP-API: enabled when `AMAZON_CLIENT_ID`, `AMAZON_CLIENT_SECRET`, and `AMAZON_REFRESH_TOKEN` are provided.
- eBay: enabled when `EBAY_APP_ID` and `EBAY_CERT_ID` are provided.
- Walmart: enabled when `WALMART_CLIENT_ID` and `WALMART_CLIENT_SECRET` are provided.
- CJ Affiliate: enabled when `CJ_ACCESS_TOKEN` is provided.
- Google Sheets: enabled when either `GOOGLE_APPLICATION_CREDENTIALS` (service account file path) or `SHEETS_LEDGER_SPREADSHEET_ID` is set.
- S3: enabled when `S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY_ID`, and `S3_SECRET_ACCESS_KEY` are provided.

If an integration is not enabled, health endpoints will show `{"enabled": false}` for that service instead of an error.

## Configuring Credentials

Set credentials via environment variables in production, using `.env.production.example` as your template. Never commit real secrets to source control.

Recommended keys:

```env
# Amazon SP-API
AMAZON_CLIENT_ID=
AMAZON_CLIENT_SECRET=
AMAZON_REFRESH_TOKEN=
AMAZON_REGION=na
AMAZON_MODE=SANDBOX

# eBay
EBAY_APP_ID=
EBAY_CERT_ID=

# Walmart
WALMART_CLIENT_ID=
WALMART_CLIENT_SECRET=
WALMART_MODE=DRYRUN

# CJ Affiliate
CJ_ACCESS_TOKEN=
CJ_BASE_URL=https://developers.cj.com

# Google Sheets
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp_service_account.json
SHEETS_LEDGER_SPREADSHEET_ID=

# S3
S3_BUCKET=
S3_REGION=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
```

For full production security, also configure:

```env
APP_ENV=production
CORS_ORIGINS=https://console.example.com
TRUSTED_HOSTS=api.example.com,console.example.com
SENTRY_DSN=
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_RESOURCE_ATTRIBUTES=service.name=marketmind-api,service.version=0.1.0,deployment.environment=production
```

## Health Endpoints

- `GET /health/data`: Returns core system health (database, redis, integrations configured flags) and timing.
- `GET /health/integrations`: Executes all integration checks and returns a structure:

```json
{
  "ok": true,
  "timestamp": "2025-09-22T03:00:00Z",
  "checks": {
    "amazon": {
      "status": true,
      "message": "Amazon SP-API connection successful",
      "details": { "latency_ms": 85, "mode": "SANDBOX" }
    },
    "sheets": {
      "status": true,
      "message": "Google Sheets connection successful",
      "details": { "latency_ms": 42, "spreadsheet_id": "..." }
    },
    "s3": {
      "status": true,
      "message": "S3 connection successful",
      "details": { "latency_ms": 30, "bucket": "...", "region": "..." }
    },
    "ebay": { "status": true, "message": "eBay not configured", "details": { "enabled": false, "latency_ms": 2 } }
  }
}
```

In the Console:
- `Integrations` page shows per-integration status with a "Test" button and latency indicator.
- `Health` page lists all checks with status filter and colored latency chips.

## Prometheus Metrics

When `prometheus_client` is installed, the API exposes `/metrics` and emits a histogram per health check:

```
# HELP health_check_latency_ms Latency of individual health checks in milliseconds
# TYPE health_check_latency_ms histogram
health_check_latency_ms_bucket{check="amazon",status="ok",le="5"} 0
health_check_latency_ms_bucket{check="amazon",status="ok",le="10"} 1
...
health_check_latency_ms_sum{check="amazon",status="ok"} 85
health_check_latency_ms_count{check="amazon",status="ok"} 1
```

Status labels are `ok` on success and `fail` on failure. If the library is missing, `/metrics` may not be mounted.

## Observability Smoke Test

Use the provided script to quickly verify health endpoints and metrics:

```bash
chmod +x scripts/observability_smoke.sh
API_BASE=http://127.0.0.1:8001 ./scripts/observability_smoke.sh
```

The script primes `/health/integrations` and checks `/metrics` for `health_check_latency_ms` lines, printing a sample if present.

## Privacy & Error Tracking

Sentry is production-gated and configured to:
- Disable sending default PII (`send_default_pii=False`).
- Scrub Authorization/Cookie headers, query strings, and user identifiers via `before_send`.
- Add breadcrumbs for failed or slow health checks when Sentry is available.

## Troubleshooting

- A check reports `enabled: false`: provide the required credentials and try again.
- `/metrics` is empty: ensure `prometheus_client` is installed in the API image and the endpoint is mounted.
- Integrations time out: verify outbound network access and credentials validity.
- CORS errors in Console: set `CORS_ORIGINS` to the Console domain and restart the API.
