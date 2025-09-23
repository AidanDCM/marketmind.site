"""
Health check probes for all integrations.

This module provides health checks for databases, external APIs, and services
to ensure the platform is operating correctly.
"""

import time
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..connectors.suppliers.cj import get_cj_adapter
from .config import get_settings
from .db import SessionLocal, engine
from .sheets import SheetsClient
from .spapi_client import SpapiClient, SpapiError


def check_database() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.time()

        # Test connection with a simple query
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "ok": True,
            "latency_ms": latency_ms,
            "engine": str(engine.url).split("://")[0],
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "latency_ms": -1}


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        import redis

        settings = get_settings()

        start_time = time.time()
        r = redis.from_url(settings.redis_url)
        r.ping()
        latency_ms = int((time.time() - start_time) * 1000)

        info = r.info()

        return {
            "ok": True,
            "latency_ms": latency_ms,
            "version": info.get("redis_version"),
            "memory_used": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
        }

    except ImportError:
        return {"ok": False, "error": "redis_not_installed"}
    except Exception as e:
        return {"ok": False, "error": str(e), "latency_ms": -1}


def check_amazon_spapi() -> Dict[str, Any]:
    """Check Amazon SP-API connectivity."""
    settings = get_settings()

    if not settings.amazon.client_id:
        return {"ok": False, "error": "not_configured", "mode": settings.amazon.mode}

    try:
        start_time = time.time()
        client = SpapiClient(
            client_id=settings.amazon.client_id,
            client_secret=settings.amazon.client_secret,
            refresh_token=settings.amazon.refresh_token,
            region=settings.amazon.region,
        )

        # Test with a small catalog request (sandbox safe)
        if settings.amazon.mode == "SANDBOX":
            # In sandbox, try to get a test ASIN
            client.get_catalog_item("B0TESTITEM")  # Sandbox test ASIN
        else:
            # In live mode, just test token refresh
            client._ensure_token()

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "ok": True,
            "latency_ms": latency_ms,
            "mode": settings.amazon.mode,
            "region": settings.amazon.region,
            "impl": settings.amazon.impl,
        }

    except SpapiError as e:
        return {"ok": False, "error": f"spapi_error: {str(e)}", "mode": settings.amazon.mode}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": settings.amazon.mode}


def check_ebay() -> Dict[str, Any]:
    """Check eBay API connectivity (sandbox)."""
    settings = get_settings()

    if not settings.ebay.app_id:
        return {"ok": False, "error": "not_configured", "mode": settings.ebay.mode}

    # For now, just return configured status
    # TODO: Implement actual eBay OAuth token test
    return {
        "ok": True,
        "latency_ms": 0,
        "mode": settings.ebay.mode,
        "status": "configured_not_tested",
    }


def check_walmart() -> Dict[str, Any]:
    """Check Walmart API configuration (DRYRUN mode)."""
    settings = get_settings()

    if not settings.walmart.client_id:
        return {"ok": False, "error": "not_configured", "mode": settings.walmart.mode}

    # In DRYRUN mode, just verify we can build signatures
    try:
        import hashlib
        import hmac

        # Test signature generation
        test_payload = '{"test": "payload"}'
        hmac.new(
            settings.walmart.client_secret.encode(), test_payload.encode(), hashlib.sha256
        ).hexdigest()

        return {
            "ok": True,
            "latency_ms": 0,
            "mode": settings.walmart.mode,
            "signature_test": "passed",
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "mode": settings.walmart.mode}


def check_cj_dropshipping() -> Dict[str, Any]:
    """Check CJ Dropshipping API connectivity."""
    try:
        cj_adapter = get_cj_adapter()
        return cj_adapter.health()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_google_sheets() -> Dict[str, Any]:
    """Check Google Sheets API connectivity."""
    try:
        client = SheetsClient()
        return client.health_check()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_s3() -> Dict[str, Any]:
    """Check S3/AWS connectivity."""
    settings = get_settings()

    if not settings.s3.bucket:
        return {"ok": False, "error": "not_configured"}

    try:
        start_time = time.time()

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.s3.access_key,
            aws_secret_access_key=settings.s3.secret_key,
            region_name=settings.s3.region,
        )

        # Test with head_bucket (minimal operation)
        s3_client.head_bucket(Bucket=settings.s3.bucket)

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "ok": True,
            "latency_ms": latency_ms,
            "bucket": settings.s3.bucket,
            "region": settings.s3.region,
        }

    except NoCredentialsError:
        return {"ok": False, "error": "credentials_not_found"}
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        return {"ok": False, "error": f"aws_error: {error_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_all_health_checks() -> Dict[str, Dict[str, Any]]:
    """Run all health checks and return results."""
    return {
        "db": check_database(),
        "redis": check_redis(),
        "amazon": check_amazon_spapi(),
        "ebay": check_ebay(),
        "walmart": check_walmart(),
        "cj": check_cj_dropshipping(),
        "sheets": check_google_sheets(),
        "s3": check_s3(),
    }


def get_health_summary() -> Dict[str, Any]:
    """Get a summary of all health checks."""
    checks = get_all_health_checks()

    all_ok = all(check.get("ok", False) for check in checks.values())
    total_checks = len(checks)
    passing_checks = sum(1 for check in checks.values() if check.get("ok", False))

    # Calculate average latency for successful checks
    latencies = [
        check["latency_ms"]
        for check in checks.values()
        if check.get("ok", False) and check.get("latency_ms", -1) > 0
    ]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    return {
        "overall_status": "healthy" if all_ok else "degraded",
        "checks_passing": passing_checks,
        "checks_total": total_checks,
        "avg_latency_ms": int(avg_latency),
        "timestamp": time.time(),
        "details": checks,
    }
