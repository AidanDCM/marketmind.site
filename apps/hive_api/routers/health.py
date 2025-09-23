import os
import time

import redis
from fastapi import APIRouter, HTTPException

from packages.shared.config import get_settings
from packages.shared.db import ping_db
from packages.shared.health import get_all_health_checks, get_health_summary

router = APIRouter()


@router.get("/live")
def live():
    return {"ok": True}


@router.get("/ready")
def ready():
    return {"ok": True}


@router.get("/data")
def data_health():
    # DB check
    t0 = time.time()
    db_status = ping_db()
    db_latency = int((time.time() - t0) * 1000)

    # Redis check
    settings = get_settings()
    r_ok = False
    r_latency = None
    r_err = None
    r_configured = False
    try:
        # Prefer REDIS_URL env var first; then fall back to typed settings.redis.url if available
        env_redis_url = os.getenv("REDIS_URL", "")
        typed_redis_url = ""
        try:
            typed_redis_url = getattr(getattr(settings, "redis", object()), "url", "") or ""
        except Exception:
            # If settings introspection raises, ignore and rely on env fallback
            typed_redis_url = ""

        redis_url = env_redis_url or typed_redis_url
        r_configured = bool(redis_url)

        r = redis.from_url(redis_url, decode_responses=True) if redis_url else None
        t1 = time.time()
        pong = r.ping() if r is not None else False
        r_latency = int((time.time() - t1) * 1000)
        r_ok = bool(pong)
    except Exception as e:
        r_err = str(e)

    # Integrations presence (env-based)
    def has(key: str):
        v = os.getenv(key)
        return v is not None and len(v) > 0

    integrations = {
        # Align with packages.shared.config.AmazonSettings field names
        "amazon_sp_api": {"configured": has("AMAZON_SP_API_REFRESH_TOKEN")},
        "ebay": {"configured": has("EBAY_APP_ID")},
        "walmart": {"configured": has("WALMART_CLIENT_ID")},
        "cj": {"configured": has("CJ_API_KEY")},
        "autods": {"configured": has("AUTODS_API_KEY")},
        "keepa": {"configured": has("KEEPA_API_KEY")},
        "gtrends": {"configured": True},
    }

    return {
        "db": {
            "ok": db_status.get("ok", False),
            "latency_ms": db_latency,
            **({"error": db_status.get("error")} if not db_status.get("ok", False) else {}),
        },
        "redis": {
            "ok": r_ok,
            "configured": r_configured,
            "latency_ms": r_latency,
            **({"error": r_err} if (not r_ok and r_err) else {}),
        },
        "integrations": integrations,
    }


@router.get("/integrations")
def integrations_health():
    """Comprehensive integration health checks with actual API probes."""
    return get_all_health_checks()


@router.get("/summary")
def health_summary():
    """Overall health summary with status and metrics."""
    return get_health_summary()


# Optional Sentry import for breadcrumbs; safe if missing
try:  # pragma: no cover - validated in prod/staging
    import sentry_sdk
except Exception:  # pragma: no cover
    sentry_sdk = None


@router.get("/slowcheck")
def slow_check(ms: int = 500, fail: bool = False):
    """Simulate a slow health probe and (optionally) a failure.

    Adds a Sentry breadcrumb (if Sentry SDK is available) noting the latency and intent.

    Query params:
    - ms: sleep duration in milliseconds (default 500)
    - fail: if true, return HTTP 500 after sleeping
    """
    t0 = time.time()
    try:
        time.sleep(max(0, ms) / 1000.0)
    finally:
        duration_ms = int((time.time() - t0) * 1000)
        if sentry_sdk is not None:
            try:
                sentry_sdk.add_breadcrumb(
                    category="health",
                    message="slowcheck",
                    level="info",
                    data={"requested_ms": ms, "duration_ms": duration_ms, "fail": bool(fail)},
                )
            except Exception:
                # never block health on telemetry
                pass

    if fail:
        raise HTTPException(status_code=500, detail={"ok": False, "duration_ms": duration_ms, "reason": "forced"})

    return {"ok": True, "duration_ms": duration_ms}
