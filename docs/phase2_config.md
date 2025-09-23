# Phase 2 Configuration System

## Overview
The Phase 2 Configuration System introduces a robust, type-safe, and auditable configuration management solution for MarketMind. It provides a centralized way to manage application settings, feature flags, and secrets across different environments.

## Key Features

### 1. Type-Safe Configuration
- All configuration is defined using Pydantic models
- Automatic environment variable parsing with validation
- Support for different environments (development, staging, production)

### 2. Secure Secret Management
- Environment-based secret loading
- Support for AWS Secrets Manager in production
- Local `.env` file support for development
- Automatic redaction of sensitive values in logs

### 3. Feature Flags
- Centralized feature flag management
- Runtime flag evaluation
- Kill switches for critical paths
- Type-safe flag access

### 4. Audit Trail
- All configuration changes are logged
- Integration with database and Google Sheets
- Redaction of sensitive values in audit logs

### 5. Health Checks
- Built-in health probes for configuration
- Integration with service health endpoints
- Detailed error reporting

## Getting Started

### Installation
No additional installation is required as the configuration system is part of the core application.

### Basic Usage

#### Accessing Configuration
```python
from packages.shared.config.loader import get_settings

# Get the current settings (cached)
settings = get_settings()

# Access configuration values
db_url = settings.db.url
amazon_client_secret = settings.amazon.client_secret  # Loaded from environment
```

#### Using Feature Flags
```python
from packages.shared.config.flags import is_simulation, FLAGS

# Short-circuit in simulation or when pricing is disabled
def publish_price(...):
    if is_simulation() or not FLAGS.is_enabled("pricing_enabled"):
        # structured log here
        return {"status": "skipped"}
    # live publish...
```

#### Secret Rotation
```bash
# Rotate a secret
python -m packages.shared.secrets.rotate --service amazon --key-id=AKIA... --secret-key=...

# Rotate multiple secrets from a file
python -m packages.shared.secrets.rotate --env-file .env.prod
```

### Environment Variables

#### Core Configuration
- `APP_ENV`: Environment name (development, staging, production)
- `CONFIG_DEBUG`: Enable debug logging for config loading
- `CONFIG_SECRETS_MANAGER`: AWS Secrets Manager ID (production only)

#### Database
- `DB_URL`: Database connection string
- `DB_POOL_SIZE`: Connection pool size
- `DB_MAX_OVERFLOW`: Maximum overflow connections

#### Amazon SP-API
- `AMAZON_CLIENT_ID`: Client ID
- `AMAZON_CLIENT_SECRET`: Client secret
- `AMAZON_REFRESH_TOKEN`: Refresh token
- `AMAZON_ROLE_ARN`: IAM role ARN
- `AMAZON_SP_API_REGION`: Region (na, eu, fe)
- `AMAZON_MODE`: SANDBOX or LIVE
- `AMAZON_IMPL`: premade or native

#### eBay
- `EBAY_APP_ID`: eBay application ID
- `EBAY_CERT_ID`: eBay certificate ID
- `EBAY_DEV_ID`: eBay developer ID
- `EBAY_REDIRECT_URI`: eBay redirect URI
- `EBAY_MODE`: SANDBOX or LIVE

#### Walmart
- `WALMART_CLIENT_ID`
- `WALMART_CLIENT_SECRET`
- `WALMART_MODE`: DRYRUN or LIVE

## Advanced Topics

### Custom Configuration Classes
You can extend the base configuration by creating new Pydantic models and including them in the `AppSettings` class.

### Adding New Feature Flags
1. Add the flag to the `FeatureFlag` enum in `packages/shared/config/flags.py`
2. Update the default values in the `FeatureFlags` model
3. Add any necessary documentation

### Secret Rotation
See the [Secrets Runbook](./secrets_runbook.md) for detailed instructions on rotating secrets in different environments.

## Best Practices

1. **Never commit secrets** to version control
2. Use environment-specific `.env` files for local development
3. Always use the `get_settings()` function to access configuration
4. Use feature flags for all new features
5. Monitor the audit logs for configuration changes

## Troubleshooting

### Common Issues

#### Configuration Not Loading
- Check that `APP_ENV` is set correctly
- Verify that required environment variables are set
- Enable `CONFIG_DEBUG=1` for detailed logging

#### Secret Rotation Fails
- Check AWS permissions for the IAM user/role
- Verify that the secret exists in AWS Secrets Manager
- Check the format of the secret JSON

## API Reference

### `get_settings() -> AppSettings`
Get the current application settings.

### `feature_flag_enabled(flag: FeatureFlag) -> bool`
Deprecated in docs. Use:
```python
from packages.shared.config.flags import FLAGS, is_simulation
FLAGS.is_enabled("pricing_enabled")
is_simulation()
```

### `with feature_flag_override(flag: FeatureFlag, enabled: bool)`
Not implemented. Prefer environment variables for runtime toggles.

### `rotate_secret(service: str, **kwargs) -> bool`
Rotate a secret for the specified service.

## Changelog

### 1.0.0 (2025-08-13)
- Initial release of Phase 2 Configuration System
