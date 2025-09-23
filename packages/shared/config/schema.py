"""
Configuration schema using Pydantic for type validation and settings management.
Defines all configuration options with their types, defaults, and environment variable bindings.
"""

import logging
import os
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Type aliases for better type hints
EnvProfile = Literal["development", "staging", "production"]
ChannelMode = Literal["SANDBOX", "LIVE", "DRYRUN", "SIMULATION"]


class DBSettings(BaseSettings):
    """Database connection settings."""

    url: str = ""
    pool_size: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo_sql: bool = False

    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    url: str = ""
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")


class AmazonSettings(BaseSettings):
    """Amazon SP-API settings."""

    impl: Literal["premade", "native"] = "premade"
    mode: ChannelMode = "SANDBOX"
    client_id: str = ""
    client_secret: str = ""
    refresh_token: str = ""
    role_arn: Optional[str] = None
    region: Literal["NA", "EU", "FE"] = "NA"

    # Pydantic v2 model config
    model_config = SettingsConfigDict(env_prefix="AMAZON_", env_file=".env", extra="ignore")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ["SANDBOX", "LIVE"]:
            raise ValueError("Amazon mode must be either 'SANDBOX' or 'LIVE'")
        return v

    # Backward-compat: support SP-API prefixed envs and region aliases
    @field_validator("client_id", mode="before")
    @classmethod
    def _fallback_client_id(cls, v):
        # Coalesce None to empty string so validation passes when unset
        return v or os.getenv("AMAZON_SP_API_CLIENT_ID") or ""

    @field_validator("client_secret", mode="before")
    @classmethod
    def _fallback_client_secret(cls, v):
        return v or os.getenv("AMAZON_SP_API_CLIENT_SECRET") or ""

    @field_validator("refresh_token", mode="before")
    @classmethod
    def _fallback_refresh_token(cls, v):
        return v or os.getenv("AMAZON_SP_API_REFRESH_TOKEN") or ""

    @field_validator("role_arn", mode="before")
    @classmethod
    def _fallback_role_arn(cls, v):
        return v or os.getenv("AMAZON_SP_API_ROLE_ARN")

    @field_validator("region", mode="before")
    @classmethod
    def _normalize_region(cls, v):
        if not v:
            v = os.getenv("AMAZON_SP_API_REGION") or os.getenv("AMAZON_REGION")
        if not v:
            return "NA"
        raw = str(v).strip().upper()
        # Map AWS regions or aliases to SP-API regions
        if raw in {"US-EAST-1", "NA", "NORTHAMERICA", "USA"}:
            return "NA"
        if raw in {"EU-WEST-1", "EU", "EUROPE"}:
            return "EU"
        if raw in {"AP-NORTHEAST-1", "FE", "FAR-EAST", "ASIA"}:
            return "FE"
        if raw in {"NA", "EU", "FE"}:
            return raw
        # Default
        return "NA"


class EbaySettings(BaseSettings):
    """eBay API settings."""

    mode: ChannelMode = "SANDBOX"
    app_id: str = ""
    cert_id: str = ""
    dev_id: str = ""
    redirect_uri: str = ""

    model_config = SettingsConfigDict(env_prefix="EBAY_", extra="ignore")


class WalmartSettings(BaseSettings):
    """Walmart Marketplace API settings."""

    mode: ChannelMode = "DRYRUN"
    client_id: str = ""
    client_secret: str = ""

    model_config = SettingsConfigDict(env_prefix="WALMART_", extra="ignore")


class CJSettings(BaseSettings):
    """CJ Affiliate API settings."""

    access_token: str = ""
    base_url: str = "https://developers.cjdropshipping.com/api2.0/v1"

    model_config = SettingsConfigDict(env_prefix="CJ_", extra="ignore")

    # Backward-compat: CJ_API_KEY -> access_token
    @field_validator("access_token", mode="before")
    @classmethod
    def _fallback_access_token(cls, v):
        # Coalesce None to empty string so validation passes when unset
        return v or os.getenv("CJ_API_KEY") or ""


class SheetsSettings(BaseSettings):
    """Google Sheets API settings."""

    service_account_json_path: str = ""
    ledger_spreadsheet_id: str = ""

    model_config = SettingsConfigDict(env_prefix="GSHEETS_", extra="ignore")

    # Backward-compat: support GSHEETS_LEDGER_ID and SHEETS_GOVERNANCE_SPREADSHEET_ID
    @field_validator("ledger_spreadsheet_id", mode="before")
    @classmethod
    def _fallback_ledger_id(cls, v):
        if v and isinstance(v, str) and v.strip():
            return v
        return os.getenv("GSHEETS_LEDGER_ID") or os.getenv("SHEETS_GOVERNANCE_SPREADSHEET_ID") or ""


class S3Settings(BaseSettings):
    """AWS S3 storage settings."""

    bucket: str = ""
    region: str = "us-east-1"
    access_key_id: str = ""
    secret_access_key: str = ""

    model_config = SettingsConfigDict(env_prefix="S3_", extra="ignore")

    # Backward-compat: allow AWS_* envs when S3_* are not set
    @field_validator("access_key_id", mode="before")
    @classmethod
    def _fallback_s3_access_key_id(cls, v):
        return v or os.getenv("S3_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID") or ""

    @field_validator("secret_access_key", mode="before")
    @classmethod
    def _fallback_s3_secret_access_key(cls, v):
        return v or os.getenv("S3_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY") or ""

    @field_validator("region", mode="before")
    @classmethod
    def _fallback_region(cls, v):
        return v or os.getenv("S3_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


class Flags(BaseSettings):
    """Feature flags and operational modes."""

    simulation_enabled: bool = True
    pricing_enabled: bool = True
    ingestion_enabled: bool = True
    orders_enabled: bool = True

    model_config = SettingsConfigDict(env_prefix="FLAG_", extra="ignore")


class AuthSettings(BaseSettings):
    """Authentication and security settings."""

    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 8  # 8 days
    cors_origins: list[str] = ["*"]
    first_superuser: str = ""
    first_superuser_password: str = ""

    # Allow fallback from CORS_ORIGINS when AUTH_CORS_ORIGINS is unset or left as "*"
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _fallback_from_plain_env(cls, v):
        # If explicit AUTH_CORS_ORIGINS provided and not wildcard, keep it
        if v and isinstance(v, list) and v != ["*"]:
            return v
        alias = os.getenv("CORS_ORIGINS")
        if alias:
            return [o.strip() for o in alias.split(",") if o.strip()]
        return v

    # Backward-compat: accept SECRET_KEY (without AUTH_ prefix)
    @field_validator("secret_key", mode="before")
    @classmethod
    def _fallback_secret_key(cls, v):
        if v and isinstance(v, str) and v.strip():
            return v
        alias = os.getenv("SECRET_KEY")
        return alias or v

    # Backward-compat: accept FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD
    @field_validator("first_superuser", mode="before")
    @classmethod
    def _fallback_first_superuser(cls, v):
        if v and isinstance(v, str) and v.strip():
            return v
        return os.getenv("FIRST_SUPERUSER") or v

    @field_validator("first_superuser_password", mode="before")
    @classmethod
    def _fallback_first_superuser_password(cls, v):
        if v and isinstance(v, str) and v.strip():
            return v
        return os.getenv("FIRST_SUPERUSER_PASSWORD") or v

    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="ignore")


class AppSettings(BaseSettings):
    """Root application settings that composes all other settings."""

    env: EnvProfile = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Service configurations
    db: DBSettings = Field(default_factory=DBSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)

    # Channel configurations
    amazon: AmazonSettings = Field(default_factory=AmazonSettings)
    ebay: EbaySettings = Field(default_factory=EbaySettings)
    walmart: WalmartSettings = Field(default_factory=WalmartSettings)
    cj: CJSettings = Field(default_factory=CJSettings)

    # Integration configurations
    sheets: SheetsSettings = Field(default_factory=SheetsSettings)
    s3: S3Settings = Field(default_factory=S3Settings)

    # Authentication and security
    auth: AuthSettings = Field(default_factory=AuthSettings)

    # Feature flags
    flags: Flags = Field(default_factory=Flags)

    # CORS settings (for backward compatibility)
    @property
    def CORS_ORIGINS(self):
        return self.auth.cors_origins

    @property
    def SECRET_KEY(self):
        return self.auth.secret_key

    @property
    def ALGORITHM(self):
        return self.auth.algorithm

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self):
        return self.auth.access_token_expire_minutes

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in ["development", "staging", "production"]:
            logging.warning(f"Invalid APP_ENV '{v}'. Defaulting to 'development'")
            return "development"
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        v = v.upper() if isinstance(v, str) else "INFO"
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging.warning(f"Invalid LOG_LEVEL '{v}'. Defaulting to 'INFO'")
            return "INFO"
        return v
