"""Slice 24: optional bearer-token API auth."""

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base

TOKEN = "secret-token-123"


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    app.state.engine = eng
    yield eng
    app.state.engine = None


def test_open_when_token_unset(engine, monkeypatch):
    monkeypatch.delenv("MARKETMIND_API_TOKEN", raising=False)
    with TestClient(app) as c:
        # A protected route works with no Authorization header.
        assert c.get("/approvals").status_code == 200


def test_protected_requires_token_when_set(engine, monkeypatch):
    monkeypatch.setenv("MARKETMIND_API_TOKEN", TOKEN)
    with TestClient(app) as c:
        # No header -> 401
        assert c.get("/approvals").status_code == 401
        # Wrong token -> 401
        assert c.get("/approvals", headers={"Authorization": "Bearer nope"}).status_code == 401
        # Correct token -> 200
        ok = c.get("/approvals", headers={"Authorization": f"Bearer {TOKEN}"})
        assert ok.status_code == 200


def test_health_always_open(engine, monkeypatch):
    monkeypatch.setenv("MARKETMIND_API_TOKEN", TOKEN)
    with TestClient(app) as c:
        # Health is reachable even with a token configured and no header.
        assert c.get("/health").status_code == 200
