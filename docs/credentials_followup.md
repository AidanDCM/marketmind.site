# Credentials & API IDs Follow-Up (Critical)

Date: 2025-08-22
Owner: MarketMind Engineering

This document lists all sensitive credentials and API IDs required for full live operation, with retrieval steps and verification commands. Phase 9 progresses without Amazon live smoke until these are completed.

## Amazon Selling Partner API (SP-API)
Required:
- AMAZON_SP_API_CLIENT_ID (LWA client id)
- AMAZON_SP_API_CLIENT_SECRET (LWA client secret)
- AMAZON_SP_API_REFRESH_TOKEN (from OAuth exchange)
- AMAZON_SP_ROLE_ARN (IAM role for SigV4, if applicable)

How to obtain refresh token:
1) Open Seller Central consent URL for your app (NA example):
   https://sellercentral.amazon.com/apps/authorize/consent?application_id=YOUR_APP_ID&state=xyz&redirect_uri=YOUR_URL_ENCODED_REDIRECT_URI
2) Capture `spapi_oauth_code` from the redirect to your `redirect_uri`.
3) Exchange code for tokens:
```bash
curl -sX POST https://api.amazon.com/auth/o2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d grant_type=authorization_code \
  -d code=SPAPI_OAUTH_CODE \
  -d client_id=$AMAZON_SP_API_CLIENT_ID \
  -d client_secret=$AMAZON_SP_API_CLIENT_SECRET \
  -d redirect_uri=YOUR_REDIRECT_URI
```
Response contains `refresh_token` → set `AMAZON_SP_API_REFRESH_TOKEN`.

Verification:
```bash
export FLAG_SIMULATION_ENABLED=false
chmod +x scripts/live_smoke.sh && ./scripts/live_smoke.sh
```
Artifacts in `reports/smoke/`.

## CJ Dropshipping
- CJ_API_KEY
- Optional: CJ_WEBSITE_ID / account identifiers as applicable
Verification:
```bash
export FLAG_SIMULATION_ENABLED=false
chmod +x scripts/live_smoke.sh && ./scripts/live_smoke.sh
```

## Google Sheets API
- GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)
- Ensure the target Sheet is shared with the service account email
Verification:
```bash
export FLAG_SIMULATION_ENABLED=false
chmod +x scripts/live_smoke.sh && ./scripts/live_smoke.sh
```

## Orders API (if enabled)
- ORDERS_API_KEY
- ORDERS_API_SECRET
- Optional auth username/password

## Security & Storage Guidance
- Never commit secrets to git; use `.env` (local only) and environment variables
- Rotate credentials on schedule; log proof-of-rotation in audit
- Use least-privilege IAM roles; restrict service account access to required scopes only

## Open Item (Amazon)
- Missing `AMAZON_SP_API_REFRESH_TOKEN` blocks Amazon live smoke.
- Phase 9 continues under waiver; return here to complete once the token is obtained.
