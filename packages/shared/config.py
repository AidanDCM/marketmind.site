from functools import lru_cache
from typing import Literal, Optional

from pydantic import BaseSettings, Field, validator

EnvProfile = Literal["development", "staging", "production"]
ChannelMode = Literal["SANDBOX", "LIVE", "DRYRUN"]


class AmazonSettings(BaseSettings):
    impl: Literal["premade", "native"] = "premade"
    mode: ChannelMode = "SANDBOX"
    client_id: str = Field(default="", env="AMAZON_SP_API_CLIENT_ID")
    client_secret: str = Field(default="", env="AMAZON_SP_API_CLIENT_SECRET")
    refresh_token: str = Field(default="", env="AMAZON_SP_API_REFRESH_TOKEN")
    role_arn: Optional[str] = Field(default=None, env="AMAZON_SP_API_ROLE_ARN")
    region: Literal["na", "eu", "fe"] = "na"
    marketplace_id: Optional[str] = Field(default=None, env="AMAZON_SP_MARKETPLACE_ID")


class EbaySettings(BaseSettings):
    mode: ChannelMode = "SANDBOX"
    app_id: str = Field(default="", env="EBAY_APP_ID")
    cert_id: str = Field(default="", env="EBAY_CERT_ID")
    dev_id: str = Field(default="", env="EBAY_DEV_ID")
    ru_name: str = Field(default="", env="EBAY_RU_NAME")


class WalmartSettings(BaseSettings):
    mode: ChannelMode = "DRYRUN"
    client_id: str = Field(default="", env="WALMART_CLIENT_ID")
    client_secret: str = Field(default="", env="WALMART_CLIENT_SECRET")


class CJSettings(BaseSettings):
    api_key: str = Field(default="", env="CJ_API_KEY")
    website_id: str = Field(default="", env="CJ_WEBSITE_ID")
    base_url: str = "https://api.cj.com/"


class SheetsSettings(BaseSettings):
    credentials_path: str = Field(default="", env="GOOGLE_APPLICATION_CREDENTIALS")
    test_sheet_id: str = Field(default="", env="GSHEETS_TEST_SHEET_ID")
    ledger_spreadsheet_id: str = Field(default="", env="GSHEETS_LEDGER_ID")


class S3Settings(BaseSettings):
    bucket: str = Field(default="", env="S3_BUCKET")
    region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    access_key: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    secret_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")


class FeatureFlags(BaseSettings):
    simulation_enabled: bool = Field(default=True, env="FEATURE_SIMULATION_ENABLED")
    pricing_enabled: bool = Field(default=True, env="FEATURE_PRICING_ENABLED")
    order_sync_enabled: bool = Field(default=True, env="FEATURE_ORDER_SYNC_ENABLED")
    inventory_sync_enabled: bool = Field(default=True, env="FEATURE_INVENTORY_SYNC_ENABLED")
    analytics_enabled: bool = Field(default=True, env="FEATURE_ANALYTICS_ENABLED")


class Settings(BaseSettings):
    # Core
    app_env: EnvProfile = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")

    # Database
    db_url: str = Field(default="sqlite:///./dev.db", env="DB_URL")
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")

    # Integrations
    amazon: AmazonSettings = AmazonSettings()
    ebay: EbaySettings = EbaySettings()
    walmart: WalmartSettings = WalmartSettings()
    cj: CJSettings = CJSettings()
    sheets: SheetsSettings = SheetsSettings()
    s3: S3Settings = S3Settings()

    # Feature Flags
    flags: FeatureFlags = FeatureFlags()

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    @validator("app_env")
    def validate_env(cls, v):
        assert v in ("development", "staging", "production"), "Invalid APP_ENV"
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Flag accessors for easy use
def simulation_enabled() -> bool:
    return get_settings().flags.simulation_enabled


def pricing_enabled() -> bool:
    return get_settings().flags.pricing_enabled


def order_sync_enabled() -> bool:
    return get_settings().flags.order_sync_enabled
