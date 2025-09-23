from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from packages.shared.config import get_settings

# Reuse the same token URL as auth router
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
settings = get_settings()


class SubjectScope:
    def __init__(self, sub: str, role: str, org_id: Optional[str], brain_ids: List[str]):
        self.sub = sub
        self.role = role
        self.org_id = org_id
        self.brain_ids = brain_ids or []

    def ensure_scope(self, req_org_id: Optional[str], req_brain_ids: List[str]) -> None:
        # Enforce org
        if req_org_id and self.org_id and req_org_id != self.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="org_id not in scope")
        # Enforce brain ids
        if req_brain_ids:
            # Wildcard support (used by dev-friendly optional scope only)
            if "*" in self.brain_ids:
                return
            missing = [b for b in req_brain_ids if b not in self.brain_ids]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="brain_id not in scope"
                )

    def require_role(self, allowed: List[str]) -> None:
        if self.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")


async def get_subject_scope(token: str = Depends(oauth2_scheme)) -> SubjectScope:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Obtain secret and algorithm with backward-compatible accessors
        try:
            secret = settings.SECRET_KEY
        except Exception:
            secret = getattr(getattr(settings, "auth", object()), "secret_key", None)
        if not secret:
            raise JWTError("missing_secret_key")

        try:
            alg = settings.ALGORITHM
        except Exception:
            alg = getattr(getattr(settings, "auth", object()), "algorithm", "HS256")

        payload = jwt.decode(token, secret, algorithms=[alg])
        sub = payload.get("sub")
        role = payload.get("role", "readonly")
        org_id = payload.get("org_id")
        brain_ids = payload.get("brain_ids", []) or []
        if not sub:
            raise cred_exc
        return SubjectScope(sub=sub, role=role, org_id=org_id, brain_ids=list(brain_ids))
    except JWTError as err:
        # Explicitly chain the credential error to distinguish handler failures
        raise cred_exc from err


async def get_subject_scope_optional(request: Request) -> SubjectScope:
    """Development-friendly scope provider.

    - If Authorization: Bearer token is present, validates it like get_subject_scope.
    - If missing and app is in development/debug, returns a permissive readonly scope.
    - If missing in non-dev, raises 401.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        return await get_subject_scope(token)  # reuse validator above

    # No token
    if (
        getattr(settings, "debug", False)
        or getattr(settings, "app_env", "development") == "development"
    ):
        # In dev, permit all brain scopes via wildcard; org remains None
        return SubjectScope(sub="dev", role="readonly", org_id=None, brain_ids=["*"])

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
