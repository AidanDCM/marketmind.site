# Amazon SP-API Configuration & Health Guide

This guide walks you through configuring Amazon Selling Partner API (SP-API) credentials, validating them safely, and integrating them with the MarketMind stack.

## Prerequisites
- Amazon SP-API Developer Account
- AWS Account (for IAM role and STS if using role-based auth)
- Seller Central access for authorization

## Required Environment Variables

Set these in your environment or CI secrets. The API supports compatibility fallbacks for some keys.

- AMAZON_SP_API_CLIENT_ID
- AMAZON_SP_API_CLIENT_SECRET
- AMAZON_SP_API_REFRESH_TOKEN
- AMAZON_SP_ROLE_ARN (optional if role-based access is used)
- AMAZON_SP_API_REGION (e.g., us-east-1)

Optional fallbacks (if used by your existing tooling):
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION (fallback for region)

## Obtaining a Refresh Token
1. Create an SP-API application in the Amazon Developer Console.
2. Configure OAuth redirect and scopes.
3. Authorize in Seller Central and obtain the authorization code.
4. Exchange for a refresh token using your client credentials.
   - Keep the refresh token secret; store in your secrets manager.

## IAM Role (Optional, Recommended)
If you use role-based access:
- Create an IAM role with the correct trust relationship for SP-API.
- Attach policies for STS and SP-API access
- Export `AMAZON_SP_ROLE_ARN` in your environment

## Local & CI Configuration

### Local (dev)
```bash
export AMAZON_SP_API_CLIENT_ID=...
export AMAZON_SP_API_CLIENT_SECRET=...
export AMAZON_SP_API_REFRESH_TOKEN=...
export AMAZON_SP_API_REGION=us-east-1
# optional if role-based
export AMAZON_SP_ROLE_ARN=arn:aws:iam::123456789012:role/SpApiRole
```

### CI (GitHub Actions)
- Add the above variables as GitHub Action Secrets
- Reference them in workflow steps for integration/backtest jobs

## Health & Smoke Checks

The system supports DRYRUN behaviors for safety in dev/CI. To validate credentials live:

- Ensure `SIMULATION_ENABLED=false` to allow real API calls
- Run integrations verification and phase backtests

```bash
make verify-integrations
make phase12-backtest
make phase13-backtest
make phase14-backtest
make phase15-backtest
```

Expected outcomes:
- SP-API endpoints respond without 401/403
- Related adapters do not return `spapi_not_configured` skips
- No PII is logged; Sentry scrubbing is active if enabled

## Troubleshooting

- 401 Unauthorized
  - Verify refresh token is current
  - Check client ID/secret
  - Ensure app is authorized for the target seller account
- 403 Forbidden
  - Check scopes and roles in Seller Central
  - Confirm IAM role trust and policies (if using role-based)
- Region Mismatch
  - Verify `AMAZON_SP_API_REGION` matches your marketplace region
- Rate Limits / Throttling
  - The system uses backoffs; repeat smokes later or lower concurrency

## Safety & Privacy
- Sentry is configured with `send_default_pii=False` and a `before_send` scrubber to prevent leakage of sensitive data (see README: Sentry Privacy Posture).
- Logs should never contain tokens or customer PII; rotate credentials if leakage is suspected.

## Related Docs
- README.md → Environment Variables / Observability / Console RBAC & Tokens
- RUNBOOK.md → Observability smokes & post-deploy checks
- CHANGELOG.md → Recent production-polish entries
