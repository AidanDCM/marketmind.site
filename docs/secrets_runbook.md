# Secrets Management Runbook

## Overview
This document provides guidelines and procedures for managing secrets in the MarketMind application. It covers secret rotation, storage, and access control.

## Table of Contents
1. [Secret Storage](#secret-storage)
2. [Secret Rotation](#secret-rotation)
3. [Emergency Procedures](#emergency-procedures)
4. [Audit Logging](#audit-logging)
5. [Best Practices](#best-practices)

## Secret Storage

### Development Environment
- Secrets are stored in `.env` files (excluded from version control)
- `.env.example` provides a template with placeholder values
- Never commit `.env` files to version control

### Production Environment
- Secrets are stored in AWS Secrets Manager
- Each environment has its own secret (e.g., `marketmind/prod`, `marketmind/staging`)
- IAM policies control access to secrets

### Secret Naming Convention
Secrets follow this naming pattern in AWS Secrets Manager:
```
marketmind/<environment>/<service>/<secret-name>
```

Example: `marketmind/prod/amazon/sp-api`

## Secret Rotation

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.8+
- Required packages: `boto3`, `python-dotenv`

### Rotating Secrets

#### 1. Amazon SP-API Credentials
```bash
# Rotate SP-API credentials
python -m packages.shared.secrets.rotate \
  --service amazon \
  --client-id <new-client-id> \
  --client-secret <new-client-secret> \
  --refresh-token <new-refresh-token> \
  --aws-access-key <aws-access-key> \
  --aws-secret-key <aws-secret-key> \
  --role-arn <role-arn>
```

#### 2. Database Credentials
```bash
# Rotate database password
python -m packages.shared.secrets.rotate \
  --service database \
  --db-url "postgresql://user:newpassword@host:5432/dbname"
```

#### 3. eBay API Credentials
```bash
# Rotate eBay credentials
python -m packages.shared.secrets.rotate \
  --service ebay \
  --app-id <app-id> \
  --cert-id <cert-id> \
  --dev-id <dev-id>
```

#### 4. Using Environment Files
For multiple secrets, create a `.env` file:
```env
# .env.prod
AMAZON_SP_API_CLIENT_ID=your-client-id
AMAZON_SP_API_CLIENT_SECRET=your-client-secret
EBAY_APP_ID=your-ebay-app-id
DB_URL=postgresql://user:password@host:5432/dbname
```

Then run:
```bash
python -m packages.shared.secrets.rotate --env-file .env.prod
```

### Automated Rotation
For production environments, set up AWS Secrets Manager's automatic rotation:

1. Create a Lambda function for rotation
2. Configure the secret to use the Lambda function
3. Set the rotation schedule (recommended: 90 days)

## Emergency Procedures

### Compromised Secrets
1. **Immediately** rotate the compromised secret using the rotation script
2. Review audit logs for suspicious access
3. If AWS credentials are compromised:
   - Rotate the AWS access keys
   - Review CloudTrail logs
   - Consider revoking all active sessions

### Lost Secrets
1. Generate new credentials for the affected service
2. Update the application configuration
3. Update the secret in AWS Secrets Manager
4. Restart affected services

## Audit Logging

### What's Logged
- All secret rotation events
- Access to sensitive configuration
- Failed authentication attempts

### Viewing Logs
1. **Database Logs**: Check the `config_audit` table
2. **CloudWatch Logs**: View logs for the Lambda rotation function
3. **AWS CloudTrail**: Monitor API calls to Secrets Manager

## Best Practices

### Development
1. Never commit secrets to version control
2. Use `.env.example` as a template
3. Set file permissions to restrict access to `.env` files

### Production
1. Use AWS Secrets Manager for all secrets
2. Enable encryption at rest and in transit
3. Rotate secrets regularly (recommended: every 90 days)
4. Use IAM roles and policies to restrict access
5. Monitor and alert on failed secret access attempts

## Secrets Hygiene Checklist (Pydantic v2 config)

Use this quick checklist before any release.

- **Inventory required env vars (by prefix)**
  - AUTH_*: `AUTH_SECRET_KEY`, `AUTH_ALGORITHM`, `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`, `AUTH_CORS_ORIGINS`, `AUTH_FIRST_SUPERUSER`, `AUTH_FIRST_SUPERUSER_PASSWORD`
  - DB_*: `DB_URL`, `DB_POOL_SIZE`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`, `DB_ECHO_SQL`
  - FLAG_*: `FLAG_SIMULATION_ENABLED`, `FLAG_PRICING_ENABLED`, `FLAG_INGESTION_ENABLED`, `FLAG_ORDERS_ENABLED`
  - AMAZON_*: `AMAZON_CLIENT_ID`, `AMAZON_CLIENT_SECRET`, `AMAZON_REFRESH_TOKEN`, `AMAZON_ROLE_ARN`, `AMAZON_REGION`, `AMAZON_MODE`
  - EBAY_*, WALMART_*, CJ_*, GSHEETS_*, S3_* as applicable

- **Scrub defaults from .env (local only)**
  - Replace placeholder defaults like `your-secret-key-here` with strong random values.
  - Never commit real secrets; keep `.env` out of VCS and update `.env.example` with safe placeholders.
  - Ensure `AUTH_CORS_ORIGINS` is set appropriately per env (avoid `*` in prod).

- **Production storage**
  - Store secrets in AWS Secrets Manager under `marketmind/<env>/<service>/<secret-name>`.
  - Rotate every 90 days; document rotations in this runbook’s appendix.

- **Verification (local)**
  - Load config: `make health-summary` (expect environment, flags, health OK).
  - Run CI security checks: `make security-check` (gitleaks + pip-audit + npm audit when applicable).
  - Initialize audit DB: `make audit-db` then confirm `config_audit` table exists.

- **Verification (runtime)**
  - POST a benign config change via app code and verify an entry appears in `config_audit` (DB) and optionally in Google Sheets if `GSHEETS_LEDGER_ID` is set.

### Example minimal `.env` (development)

```env
# Core
APP_ENV=development
DEBUG=true

# Auth
AUTH_SECRET_KEY=dev-please-change
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=2880
AUTH_CORS_ORIGINS=["http://127.0.0.1:8001"]
AUTH_FIRST_SUPERUSER=admin@example.com
AUTH_FIRST_SUPERUSER_PASSWORD=dev-password-change

# DB
DB_URL=sqlite:///./dev.db
DB_POOL_SIZE=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO_SQL=false

# Feature flags
FLAG_SIMULATION_ENABLED=true
FLAG_PRICING_ENABLED=true
FLAG_INGESTION_ENABLED=true
FLAG_ORDERS_ENABLED=true
```

### General
1. Use different secrets for different environments
2. Document all secret rotations
3. Test rotation procedures in staging first
4. Have a rollback plan for failed rotations

## Environment Variables Glossary

Short descriptions of the most important env vars. Place real values only in your local `.env` or a secret manager; never commit them.

- AMAZON_SP_API_CLIENT_ID: LWA Client ID for your Amazon SP-API app (Seller Central → Developer Console).
- AMAZON_SP_API_CLIENT_SECRET: LWA Client Secret for your Amazon SP-API app.
- AMAZON_SP_API_REFRESH_TOKEN: Long-lived token returned after seller consents your app; used to obtain access tokens.
- AMAZON_SP_API_ROLE_ARN: IAM role ARN used for SP-API (e.g., arn:aws:iam::...:role/SPAPIRole-NA).
- AMAZON_SP_API_REGION: AWS region for SP-API calls (e.g., us-east-1 for NA).
- AMAZON_SP_API_MARKETPLACE_IDS: Comma-separated marketplace IDs (US: ATVPDKIKX0DER; add others as needed).
- AMAZON_MODE: SANDBOX or LIVE mode for Amazon operations.
- AMAZON_IMPL: Implementation mode: premade or native.

- AWS_ACCESS_KEY_ID: Access key for an IAM user allowed to assume the SP-API role (sts:AssumeRole).
- AWS_SECRET_ACCESS_KEY: Secret for the above access key.
- AWS_SESSION_TOKEN: Session token when using temporary credentials (optional).

- CJ_API_KEY: Commission Junction (CJ) API key for dropshipping adapter.
- CJ_WEBSITE_ID: Your CJ website/site ID if required by your workflows.

- GOOGLE_APPLICATION_CREDENTIALS: Absolute path to Google service account JSON with Sheets API enabled.
- SHEETS_GOVERNANCE_SPREADSHEET_ID: Target Google Sheet ID for operational logs/entries (optional; copy from the sheet URL).
- GSHEETS_LEDGER_ID: Test/ledger sheet used by health checks (optional).

- EBAY_APP_ID: eBay application ID (sandbox or live).
- EBAY_CERT_ID: eBay certificate (client secret) ID.
- EBAY_DEV_ID: eBay developer ID.
- EBAY_REDIRECT_URI: Redirect URI registered with eBay application.
- EBAY_MODE: SANDBOX or LIVE mode for eBay operations.
- EBAY_USER_TOKEN: eBay user token (sandbox/live) when required by API calls.

- DB_URL: Database URL (e.g., sqlite:///./dev.db for local development).
- SECRET_KEY: App secret for JWT and crypto (use strong random in production).
- APP_ENV: Environment (development, staging, production).
- FLAG_SIMULATION_ENABLED: Enables simulated flows instead of real external calls in some adapters.

## Troubleshooting

### Rotation Fails
1. Check IAM permissions for the rotation Lambda function
2. Verify the secret exists in Secrets Manager
3. Check CloudWatch logs for error messages

### Application Can't Access Secrets
1. Verify IAM role permissions
2. Check network connectivity to Secrets Manager
3. Verify the secret ARN in the application configuration

## Appendix: Required IAM Permissions

### For Secret Rotation
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:PutSecretValue",
                "secretsmanager:UpdateSecretVersionStage"
            ],
            "Resource": "arn:aws:secretsmanager:region:account-id:secret:marketmind/*"
        }
    ]
}
```

### For Application Access
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:region:account-id:secret:marketmind/*"
        }
    ]
}
```
