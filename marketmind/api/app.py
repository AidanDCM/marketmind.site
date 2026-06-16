"""Slice 13: FastAPI application factory.

Usage:
    uvicorn marketmind.api.app:app --reload

The engine is created lazily on startup from DATABASE_URL. Tests
inject a test engine via app.state.engine before calling TestClient.

Schema management:
- Production/file DBs: Alembic runs `upgrade head` on startup so the schema
  is always at the latest migration without manual intervention.
- In-memory SQLite (tests): create_all is used because Alembic needs a real
  file URL to store migration state; tests inject the engine directly.
"""

from __future__ import annotations

import os
import pathlib
from contextlib import asynccontextmanager

from alembic.config import Config as AlembicConfig
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from alembic import command as alembic_cmd

from ..db.engine import make_engine
from ..db.models import Base
from ..logging_config import setup_logging
from .auth import install_auth
from .routers import (
    approvals,
    economics,
    execution,
    experiments,
    health,
    imports,
    pipeline,
    reports,
    scoring,
    snapshots,
    sources,
    spec,
)

_ALEMBIC_INI = pathlib.Path(__file__).resolve().parents[2] / "alembic.ini"


def _run_migrations(db_url: str) -> None:
    cfg = AlembicConfig(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cmd.upgrade(cfg, "head")


@asynccontextmanager
async def _lifespan(application: FastAPI):
    setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
    if not hasattr(application.state, "engine") or application.state.engine is None:
        engine = make_engine()
        db_url = str(engine.url)
        if db_url.startswith("sqlite:///"):
            pathlib.Path(db_url.removeprefix("sqlite:///")).parent.mkdir(
                parents=True, exist_ok=True
            )
        # Use Alembic migrations for real file DBs; create_all for in-memory.
        if db_url == "sqlite:///:memory:":
            Base.metadata.create_all(engine)
        else:
            _run_migrations(db_url)
        application.state.engine = engine
    yield


app = FastAPI(
    title="MarketMind Autopilot",
    version="0.2.0",
    description="Human-in-the-loop commerce operating system.",
    lifespan=_lifespan,
)


@app.exception_handler(ValueError)
async def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


install_auth(app)


app.include_router(health.router)
app.include_router(scoring.router, prefix="/score")
app.include_router(spec.router, prefix="/spec")
app.include_router(approvals.router, prefix="/approvals")
app.include_router(reports.router, prefix="/report")
app.include_router(economics.router, prefix="/economics")
app.include_router(experiments.router, prefix="/experiment")
app.include_router(pipeline.router, prefix="/pipeline")
app.include_router(execution.router, prefix="/execute")
app.include_router(sources.router, prefix="/sources")
app.include_router(imports.router, prefix="/imports")
app.include_router(snapshots.router, prefix="/snapshots")
