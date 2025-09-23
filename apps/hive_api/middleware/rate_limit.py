import time
from typing import Dict, Tuple

from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Simple in-memory fixed-window limiter for development
# Scope: per-IP per-path, 5 requests per 60 seconds
WINDOW_SECONDS = 60
MAX_REQUESTS = 5

# key: (ip, path) -> (count, reset_epoch_seconds)
_store: Dict[Tuple[str, str], Tuple[int, float]] = {}


async def limiter_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    # Apply only to the sensitive auth token endpoint in dev
    # This prevents accidental brute force during local testing
    path = request.url.path
    if path == "/auth/token":
        now = time.time()
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, path)
        count, reset_at = _store.get(key, (0, now + WINDOW_SECONDS))
        if now > reset_at:
            # Reset window
            count = 0
            reset_at = now + WINDOW_SECONDS
        count += 1
        _store[key] = (count, reset_at)
        if count > MAX_REQUESTS:
            retry_after = max(0, int(reset_at - now))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many authentication attempts. Please try again later.",
                },
                headers={"Retry-After": str(retry_after)},
            )

    return await call_next(request)
