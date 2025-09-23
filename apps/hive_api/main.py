import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Ensure models are imported so metadata is populated
import packages.database.models  # noqa: F401
from apps.hive_api.routers import (
    ai,
    auth,
    compliance,
    dash,
    demo,
    finance,
    health,
    ingest,
    learning,
    marketing,
    orchestrator,
    orders,
    pricing,
    pricing_sim,
    privacy,
    profit,
    tax,
)
from packages.database.models.base import Base as ModelsBase
from packages.shared.config import get_settings
from packages.shared.db import get_db, get_engine

# Optional observability & rate limiting imports
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
except ImportError:  # pragma: no cover
    sentry_sdk = None
    FastApiIntegration = None
    SqlalchemyIntegration = None

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:  # pragma: no cover
    FastAPIInstrumentor = None

try:
    from prometheus_client import make_asgi_app as prometheus_asgi_app
except ImportError:  # pragma: no cover
    prometheus_asgi_app = None

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
except ImportError:  # pragma: no cover
    Limiter = None
    SlowAPIMiddleware = None
    RateLimitExceeded = None
    _rate_limit_exceeded_handler = None
    get_remote_address = None

# Initialize settings
settings = get_settings()

# Initialize rate limiter if available
if Limiter is not None:
    # Prefer Redis if configured; otherwise fall back to in-memory storage for dev/local
    storage_uri = os.getenv("REDIS_URL") or "memory://"
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,
    )
else:
    limiter = None

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # CSP for API (restrictive)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        
        # HSTS (if HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize application services
    engine = get_engine()
    # In non-production environments, auto-create tables for faster DX.
    # Production uses migrations-only strategy per security guidelines.
    if settings.env != "production":
        # Use the models Base so all model tables are created in dev
        ModelsBase.metadata.create_all(bind=engine)

    # Create default admin user if it doesn't exist (dev/staging convenience)
    db = next(get_db())
    try:
        from apps.hive_api.routers.auth import get_password_hash
        from packages.database.models.user import User

        # Use settings.auth for initial superuser
        admin_email = settings.auth.first_superuser
        admin_password = settings.auth.first_superuser_password

        if settings.env != "production" and admin_email and admin_password:
            user = db.query(User).filter(User.email == admin_email).first()
            if not user:
                db_user = User(
                    username=admin_email.split("@")[0] if "@" in admin_email else admin_email,
                    email=admin_email,
                    hashed_password=get_password_hash(admin_password),
                    first_name="Admin",
                    last_name="User",
                    is_superuser=True,
                )
                db.add(db_user)
                db.commit()
    except Exception as e:
        # Log the error but don't crash the app
        print(f"Error creating default admin user: {e}")
    finally:
        db.close()

    yield
    # Shutdown: no-op for now


# Configure FastAPI docs based on environment
docs_config = {}
if settings.env == "production":
    # Disable all documentation endpoints in production
    docs_config = {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }
    print(f"[SECURITY] API docs disabled for production environment (APP_ENV={settings.env})")
else:
    # Enable documentation in development/staging
    docs_config = {
        "docs_url": "/docs",
        "redoc_url": "/redoc", 
        "openapi_url": "/openapi.json",
    }
    print(f"[INFO] API docs enabled for {settings.env} environment")

app = FastAPI(
    title="Hive API",
    version="1.0.0",
    description="MarketMind E-commerce Automation Platform API",
    lifespan=lifespan,
    **docs_config,
)

# Initialize observability
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if settings.env == "production" and SENTRY_DSN and sentry_sdk:
    # Scrub PII and sensitive headers from events before sending
    def _sentry_before_send(event, hint):  # pragma: no cover - behavior validated in prod
        try:
            # Remove request cookies, authorization headers, query strings
            request = event.get("request", {})
            headers = request.get("headers", {})
            # Strip common sensitive headers
            for h in [
                "authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token",
                "x-forwarded-for", "x-real-ip",
            ]:
                if h in headers:
                    headers[h] = "[scrubbed]"
            request["headers"] = headers
            # Remove cookies and query strings
            if "cookies" in request:
                request["cookies"] = "[scrubbed]"
            if "query_string" in request:
                request["query_string"] = "[scrubbed]"
            event["request"] = request

            # Remove user identifying fields if present
            user = event.get("user", {})
            for k in ["email", "username", "ip_address", "id"]:
                if k in user:
                    user[k] = "[scrubbed]"
            event["user"] = user
        except Exception:
            # Fail-open but do not block event reporting
            pass
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=settings.env,
        # Strong privacy defaults
        send_default_pii=False,
        before_send=_sentry_before_send,
    )

# OpenTelemetry instrumentation
if FastAPIInstrumentor is not None:
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception:  # pragma: no cover
        pass

# Dev-only simple in-process rate limiter middleware for /auth/token
# Used when SlowAPI/Redis are unavailable (non-production only)
_dev_rate_limit_state: dict[str, list[float]] = {}

async def limiter_middleware(request: Request, call_next):  # pragma: no cover - dev utility
    try:
        if request.url.path == "/auth/token":
            now = time.time()
            ip = request.client.host if request.client else "unknown"
            window = 60.0
            limit = 5
            timestamps = _dev_rate_limit_state.get(ip, [])
            # keep only requests in the last window seconds
            timestamps = [t for t in timestamps if now - t < window]
            if len(timestamps) >= limit:
                return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
            timestamps.append(now)
            _dev_rate_limit_state[ip] = timestamps
    except Exception:
        # fail open in dev
        pass
    return await call_next(request)

# Rate limiting setup
if limiter is not None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

# Dev-only fallback rate limiter when SlowAPI/Redis is unavailable
if limiter is None and settings.env != "production":
    # Simple per-process in-memory limiter to protect /auth/token during local dev
    app.middleware("http")(limiter_middleware)

# Trusted Host middleware (protect against Host header attacks)
trusted_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
if settings.env == "production":
    # Add production domains from environment
    production_hosts = os.getenv("TRUSTED_HOSTS", "").split(",")
    trusted_hosts.extend([host.strip() for host in production_hosts if host.strip()])

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS (restrictive for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Mount Prometheus metrics if available
if prometheus_asgi_app is not None:
    app.mount("/metrics", prometheus_asgi_app())

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, tags=["auth"])
app.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
app.include_router(pricing_sim.router, prefix="/pricing", tags=["pricing"])
app.include_router(ingest.router, tags=["ingestion"])
app.include_router(orchestrator.router, tags=["orchestrator"])
app.include_router(orders.router)
app.include_router(dash.router)
app.include_router(profit.router, prefix="/profit", tags=["profit"])
app.include_router(compliance.router, tags=["compliance"])
app.include_router(privacy.router, tags=["privacy"])
app.include_router(tax.router, tags=["tax"])
app.include_router(marketing.router, prefix="/marketing", tags=["marketing"])
app.include_router(finance.router, tags=["finance"])
app.include_router(learning.router, tags=["learning"])
app.include_router(ai.router, tags=["ai"])
if settings.env != "production":
    app.include_router(demo.router)


# Root endpoint
@app.get("/_info")
async def info():
    return {
        "app": "MarketMind Hive API",
        "version": "1.0.0",
        "environment": settings.env,
        "debug": settings.debug,
    }


# Root route – developer friendly in non-production
@app.get("/")
async def root():
    # Redirect to interactive docs in development/staging; return JSON in production
    if settings.env != "production":
        return RedirectResponse(url="/docs")
    return JSONResponse({"status": "ok", "app": "MarketMind Hive API"})


# Removed deprecated on_event startup; handled in lifespan above
