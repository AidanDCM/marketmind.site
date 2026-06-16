"""Optional bearer-token authentication for the API.

Security posture:
  - If MARKETMIND_API_TOKEN is set in the environment, every request must carry
    ``Authorization: Bearer <token>`` (constant-time compared). Missing/incorrect
    tokens get 401.
  - If the variable is unset, the API is open — the local-dev default, so the
    desktop app works against localhost with no setup. A warning is logged once
    so an unauthenticated deployment is never silent.
  - A small allowlist (health + API docs) is always reachable so liveness checks
    and the OpenAPI UI work even when a token is configured.

This is intentionally simple (a single shared token). It is the floor that lets
the backend leave localhost safely; richer auth (per-user, rotation) can build
on top later.
"""

from __future__ import annotations

import hmac
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..logging_config import get_logger

log = get_logger(__name__)

# Always reachable without a token.
_OPEN_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

_ENV_VAR = "MARKETMIND_API_TOKEN"


def _expected_token() -> str:
    return os.environ.get(_ENV_VAR, "").strip()


def install_auth(app: FastAPI) -> None:
    """Attach the bearer-token middleware to the app."""

    @app.middleware("http")
    async def _bearer_auth(request: Request, call_next):
        token = _expected_token()
        if token and request.url.path not in _OPEN_PATHS:
            provided = request.headers.get("Authorization", "")
            if not hmac.compare_digest(provided, f"Bearer {token}"):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)

    if not _expected_token():
        log.warning(
            "API auth is OFF (%s not set). Safe for localhost; set a token "
            "before exposing the API beyond this machine.",
            _ENV_VAR,
        )
