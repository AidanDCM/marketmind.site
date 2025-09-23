"""
Health check probes for the MarketMind application.

This module contains functions to verify the health of various components
and dependencies, including configuration and credentials.
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel

from ..config import get_flags, get_settings

# Optional Prometheus histogram for health check latencies
try:  # pragma: no cover - optional dependency
    from prometheus_client import Histogram  # type: ignore

    HEALTH_CHECK_LATENCY = Histogram(
        "health_check_latency_ms",
        "Latency of individual health checks in milliseconds",
        labelnames=("check", "status"),
        buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
    )
except Exception:  # pragma: no cover
    HEALTH_CHECK_LATENCY = None  # type: ignore

logger = logging.getLogger(__name__)

# Optional Sentry for breadcrumbs/capture on failures or slow checks
try:  # pragma: no cover - optional dependency
    import sentry_sdk  # type: ignore
except Exception:  # pragma: no cover
    sentry_sdk = None  # type: ignore

def _sentry_breadcrumb(level: str, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Add a Sentry breadcrumb if Sentry is available.

    This is safe-noop when Sentry is not installed.
    """
    if sentry_sdk is None:
        return
    try:  # pragma: no cover - observational
        sentry_sdk.add_breadcrumb(
            type="default",
            category=category,
            message=message,
            level=level,
            data=data or {},
        )
    except Exception:
        # Never raise from observability helpers
        pass

def _sentry_capture_message(message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
    if sentry_sdk is None:
        return
    try:  # pragma: no cover - observational
        if data:
            # attach context data via breadcrumb for compactness
            _sentry_breadcrumb(level=level, category="health.check", message=message, data=data)
        sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


class HealthCheckResult(BaseModel):
    """Result of a health check."""

    status: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.dict()


class HealthChecker:
    """Performs health checks on the application and its dependencies."""

    def __init__(self):
        self.settings = get_settings()
        self.flags = get_flags()
        self.checks: Dict[str, Callable[[], HealthCheckResult]] = {
            "config": self.check_config,
            "database": self.check_database,
            "redis": self.check_redis,
            "amazon": self.check_amazon,
            "ebay": self.check_ebay,
            "walmart": self.check_walmart,
            "cj": self.check_cj,
            "sheets": self.check_sheets,
            "s3": self.check_s3,
        }

    def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks and return the results."""
        results = {}
        for name, check_func in self.checks.items():
            start = time.perf_counter()
            try:
                result = check_func()
                # Attach latency to details
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                details = result.details.copy() if result.details else {}
                details["latency_ms"] = elapsed_ms
                result.details = details
                results[name] = result
                # Observe metric with correct status label
                if HEALTH_CHECK_LATENCY is not None:  # pragma: no cover
                    HEALTH_CHECK_LATENCY.labels(check=name, status=("ok" if result.status else "fail")).observe(elapsed_ms)
                # Sentry breadcrumbs for failures or slow checks
                if not result.status:
                    _sentry_breadcrumb(
                        level="error",
                        category="health.check",
                        message=f"Health check failed: {name}",
                        data={"latency_ms": elapsed_ms, "message": result.message},
                    )
                    _sentry_capture_message(
                        message=f"Health check failed: {name}",
                        level="error",
                        data={"latency_ms": elapsed_ms},
                    )
                elif elapsed_ms >= 500:
                    _sentry_breadcrumb(
                        level="warning",
                        category="health.check.slow",
                        message=f"Slow health check: {name}",
                        data={"latency_ms": elapsed_ms},
                    )
            except Exception as e:
                logger.exception(f"Health check '{name}' failed with error")
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if HEALTH_CHECK_LATENCY is not None:  # pragma: no cover
                    HEALTH_CHECK_LATENCY.labels(check=name, status="fail").observe(elapsed_ms)
                results[name] = HealthCheckResult(
                    status=False,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e), "latency_ms": elapsed_ms},
                )
                _sentry_breadcrumb(
                    level="error",
                    category="health.check",
                    message=f"Health check exception: {name}",
                    data={"latency_ms": elapsed_ms, "error": str(e)},
                )
                _sentry_capture_message(
                    message=f"Health check exception: {name}",
                    level="error",
                    data={"latency_ms": elapsed_ms},
                )
        return results

    def check_config(self) -> HealthCheckResult:
        """Check that required configuration is present."""
        missing = []

        # Check required settings
        if not self.settings.db.url:
            missing.append("DB_URL")
        # Redis is optional in dev/local; don't require REDIS_URL for baseline config

        # If any Amazon credential is provided, ensure required fields are present
        if (
            getattr(self.settings.amazon, "client_id", "")
            or getattr(self.settings.amazon, "client_secret", "")
            or getattr(self.settings.amazon, "refresh_token", "")
        ):
            if not self.settings.amazon.client_id:
                missing.append("AMAZON_CLIENT_ID")
            if not self.settings.amazon.client_secret:
                missing.append("AMAZON_CLIENT_SECRET")

        if missing:
            return HealthCheckResult(
                status=False,
                message=f"Missing required configuration: {', '.join(missing)}",
                details={"missing": missing},
            )

        return HealthCheckResult(
            status=True,
            message="All required configuration is present",
            details={"environment": self.settings.env},
        )

    def check_database(self) -> HealthCheckResult:
        """Check database connection."""
        from sqlalchemy import create_engine, text

        try:
            url = self.settings.db.url
            # SQLite does not support the connect_args we use for Postgres
            if isinstance(url, str) and url.startswith("sqlite"):
                engine = create_engine(url, pool_pre_ping=True)
            else:
                engine = create_engine(
                    url,
                    connect_args={"connect_timeout": 5, "options": "-c statement_timeout=5000"},
                    pool_pre_ping=True,
                )

            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    raise ValueError("Unexpected result from database")

            return HealthCheckResult(
                status=True,
                message="Database connection successful",
                details={
                    "url": self._redact_url(self.settings.db.url),
                    "pool_size": self.settings.db.pool_size,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"Database connection failed: {str(e)}",
                details={
                    "url": (
                        self._redact_url(self.settings.db.url)
                        if hasattr(self.settings, "db")
                        else "Not configured"
                    )
                },
            )

    def check_redis(self) -> HealthCheckResult:
        """Check Redis connection."""
        try:
            import redis

            url = getattr(self.settings.redis, "url", "")
            if not url:
                return HealthCheckResult(
                    status=True, message="Redis not configured", details={"enabled": False}
                )
            r = redis.Redis.from_url(
                url, socket_connect_timeout=2, socket_timeout=2, retry_on_timeout=False
            )

            # Test connection
            if not r.ping():
                raise RuntimeError("Ping failed")

            return HealthCheckResult(
                status=True,
                message="Redis connection successful",
                details={"url": self._redact_url(url)},
            )

        except Exception as e:
            # In development, Redis is optional; treat as non-fatal
            if getattr(self.settings, "env", "development") == "development":
                return HealthCheckResult(
                    status=True,
                    message="Redis not configured (dev optional)",
                    details={"enabled": False},
                )
            return HealthCheckResult(
                status=False,
                message=f"Redis connection failed: {str(e)}",
                details={
                    "url": (
                        self._redact_url(getattr(self.settings.redis, "url", ""))
                        if hasattr(self.settings, "redis")
                        else "Not configured"
                    )
                },
            )

    def check_amazon(self) -> HealthCheckResult:
        """Check Amazon SP-API connection."""
        # Consider Amazon disabled unless all core credentials are provided
        if not (
            getattr(self.settings.amazon, "client_id", "")
            and getattr(self.settings.amazon, "client_secret", "")
            and getattr(self.settings.amazon, "refresh_token", "")
        ):
            return HealthCheckResult(
                status=True, message="Amazon not configured", details={"enabled": False}
            )

        try:
            # Import here to avoid circular imports
            from ..spapi_client import SPAPIClient

            client = SPAPIClient()

            # Simple API call to check credentials
            if getattr(self.settings.amazon, "mode", "SANDBOX") == "SANDBOX":
                client.get_catalog_item(asin="B07PGL7P7D", marketplace_id="ATVPDKIKX0DER")
            else:
                # In production, use a lightweight operation
                client.get_marketplace_participations()

            return HealthCheckResult(
                status=True,
                message="Amazon SP-API connection successful",
                details={
                    "mode": self.settings.amazon.mode,
                    "region": self.settings.amazon.region,
                    "implementation": self.settings.amazon.impl,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"Amazon SP-API connection failed: {str(e)}",
                details={"mode": getattr(self.settings.amazon, "mode", "unknown"), "error": str(e)},
            )

    def check_ebay(self) -> HealthCheckResult:
        """Check eBay API connection."""
        # Dynamically enable based on presence of credentials; otherwise treat as not configured
        ebay_cfg = getattr(self.settings, "ebay", object())
        has_creds = bool(getattr(ebay_cfg, "app_id", "") and getattr(ebay_cfg, "cert_id", ""))
        if not has_creds:
            return HealthCheckResult(
                status=True, message="eBay not configured", details={"enabled": False}
            )

        try:
            # Prefer connectors package path; gracefully skip if unavailable
            from packages.connectors.channels.ebay import EBayAdapter  # type: ignore

            client = EBayAdapter()
            hc = client.health()
            if hc.get("ok"):
                return HealthCheckResult(
                    status=True,
                    message="eBay API connection successful",
                    details={"sandbox": hc.get("sandbox", True)},
                )
            else:
                return HealthCheckResult(
                    status=False,
                    message=f"eBay API connection failed: {hc.get('error', 'unknown')}",
                    details={"sandbox": hc.get("sandbox", True)},
                )

        except ImportError:
            return HealthCheckResult(
                status=True, message="eBay adapter not available", details={"enabled": False}
            )
        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"eBay API connection failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_walmart(self) -> HealthCheckResult:
        """Check Walmart API connection."""
        # Dynamically enable based on presence of credentials; otherwise treat as not configured
        wm_cfg = getattr(self.settings, "walmart", object())
        has_creds = bool(getattr(wm_cfg, "client_id", "") and getattr(wm_cfg, "client_secret", ""))
        if not has_creds:
            return HealthCheckResult(
                status=True, message="Walmart not configured", details={"enabled": False}
            )

        try:
            # Prefer connectors package path; gracefully skip if unavailable
            from packages.connectors.channels.walmart import WalmartAdapter  # type: ignore

            client = WalmartAdapter()

            # Use adapter's health probe
            hc = client.health()
            # Prefer settings-based mode evaluation
            if getattr(self.settings.walmart, "mode", "DRYRUN") == "DRYRUN":
                return HealthCheckResult(
                    status=True, message="Walmart API is in DRYRUN mode", details={"mode": "DRYRUN"}
                )
            if hc.get("ok"):
                return HealthCheckResult(
                    status=True,
                    message="Walmart API connection successful",
                    details={"sandbox": hc.get("sandbox", True)},
                )
            return HealthCheckResult(
                status=False,
                message=f"Walmart API connection failed: {hc.get('error', 'unknown')}",
                details={"sandbox": hc.get("sandbox", True)},
            )

        except ImportError:
            return HealthCheckResult(
                status=True, message="Walmart adapter not available", details={"enabled": False}
            )
        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"Walmart API connection failed: {str(e)}",
                details={"mode": getattr(self.settings.walmart, "mode", "unknown")},
            )

    def check_cj(self) -> HealthCheckResult:
        """Check CJ Affiliate API connection."""
        cj_cfg = getattr(self.settings, "cj", object())
        # Credential-driven enablement based on access_token (CJ_API_KEY fallback handled in schema)
        has_creds = bool(getattr(cj_cfg, "access_token", ""))
        if not has_creds:
            return HealthCheckResult(
                status=True, message="CJ not configured", details={"enabled": False}
            )

        try:
            # Import here to avoid circular imports
            from ..adapters.cj import CJAdapter

            client = CJAdapter()
            # Lightweight fetch to validate credentials/connectivity
            client.fetch_products(limit=1)

            return HealthCheckResult(
                status=True,
                message="CJ API connection successful",
                details={"base_url": getattr(self.settings.cj, "base_url", None)},
            )

        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"CJ API connection failed: {str(e)}",
                details={"base_url": getattr(self.settings.cj, "base_url", "Not configured"), "error": str(e)},
            )

    def check_sheets(self) -> HealthCheckResult:
        """Check Google Sheets API connection."""
        # Treat as not configured unless explicit credentials path or config present
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not creds_path and not getattr(getattr(self.settings, "sheets", object()), "ledger_spreadsheet_id", ""):
            return HealthCheckResult(
                status=True,
                message="Google Sheets not configured",
                details={"enabled": False},
            )

        try:
            # Import here to avoid circular imports
            from ..sheets import SheetsClient

            client = SheetsClient()
            hc = client.health_check()
            if not hc.get("ok"):
                return HealthCheckResult(
                    status=False,
                    message=f"Google Sheets connection failed: {hc.get('error', 'unknown')}",
                    details=hc,
                )

            return HealthCheckResult(
                status=True,
                message="Google Sheets connection successful",
                details={k: v for k, v in hc.items() if k in {"latency_ms", "spreadsheet_id"}},
            )

        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"Google Sheets connection failed: {str(e)}",
                details={
                    "spreadsheet_id": getattr(self.settings.sheets, "ledger_spreadsheet_id", "Not configured"),
                    "error": str(e),
                },
            )

    def check_s3(self) -> HealthCheckResult:
        """Check S3 connection and permissions."""
        s3_cfg = getattr(self.settings, "s3", object())
        has_cfg = bool(getattr(s3_cfg, "bucket", "") and getattr(s3_cfg, "region", ""))
        # Schema fields are access_key_id/secret_access_key (env prefix S3_*)
        has_keys = bool(getattr(s3_cfg, "access_key_id", "") and getattr(s3_cfg, "secret_access_key", ""))
        if not has_cfg or not has_keys:
            return HealthCheckResult(
                status=True, message="S3 not configured", details={"enabled": False}
            )

        try:
            import boto3
            from botocore.exceptions import ClientError

            s3 = boto3.client(
                "s3",
                aws_access_key_id=self.settings.s3.access_key_id or None,
                aws_secret_access_key=self.settings.s3.secret_access_key or None,
                region_name=self.settings.s3.region,
            )

            # Test connection and permissions
            s3.head_bucket(Bucket=self.settings.s3.bucket)

            return HealthCheckResult(
                status=True,
                message="S3 connection successful",
                details={"bucket": self.settings.s3.bucket, "region": self.settings.s3.region},
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            return HealthCheckResult(
                status=False,
                message=f"S3 connection failed: {error_code}",
                details={
                    "bucket": getattr(self.settings.s3, "bucket", "Not configured"),
                    "error": str(e),
                },
            )
        except Exception as e:
            return HealthCheckResult(
                status=False,
                message=f"S3 connection failed: {str(e)}",
                details={
                    "bucket": getattr(self.settings.s3, "bucket", "Not configured"),
                    "error": str(e),
                },
            )

    def _redact_url(self, url: str) -> str:
        """Redact sensitive information from URLs."""
        if not url:
            return ""

        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(url)

            # Redact username and password
            if parsed.username or parsed.password:
                netloc = f"{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"

                # Create new URL with redacted credentials
                return urlunparse(
                    parsed._replace(
                        netloc=netloc,
                        query="",  # Remove query string which might contain sensitive data
                    )
                )

            return url

        except Exception:
            # If anything goes wrong, return a redacted version
            if "@" in url:
                # Basic redaction for URLs with credentials
                return "[REDACTED]@" + url.split("@", 1)[1]
            return "[REDACTED]"


def get_health() -> Dict[str, Any]:
    """Get the health status of the application and its dependencies."""
    checker = HealthChecker()
    results = checker.check_all()

    # Determine overall status
    all_healthy = all(result.status for result in results.values())
    status = "healthy" if all_healthy else "degraded"

    # Count checks by status
    status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}
    for result in results.values():
        if result.status:
            status_counts["healthy"] += 1
        else:
            status_counts["unhealthy"] += 1

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {name: result.to_dict() for name, result in results.items()},
        "summary": {
            "total": len(results),
            "healthy": status_counts["healthy"],
            "unhealthy": status_counts["unhealthy"],
            "degraded": 0,  # Not currently tracking degraded separately
        },
    }


def get_all_health_checks() -> Dict[str, Any]:
    """Return detailed results for all integration health checks.

    This is intended for the `/health/integrations` endpoint.
    """
    checker = HealthChecker()
    results = checker.check_all()

    overall_ok = all(r.status for r in results.values())
    return {
        "ok": overall_ok,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {name: result.to_dict() for name, result in results.items()},
    }


def get_health_summary() -> Dict[str, Any]:
    """Return a summarized view of overall health with counts and status."""
    checker = HealthChecker()
    results = checker.check_all()

    healthy = sum(1 for r in results.values() if r.status)
    unhealthy = sum(1 for r in results.values() if not r.status)
    status = "healthy" if unhealthy == 0 else "degraded"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "total_checks": len(results),
            "healthy": healthy,
            "unhealthy": unhealthy,
        },
    }
