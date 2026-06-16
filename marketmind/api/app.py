"""Slice 13: FastAPI application factory.

Usage:
    uvicorn marketmind.api.app:app --reload

The engine is created lazily on startup from DATABASE_URL. Tests
inject a test engine via app.state.engine before calling TestClient.
"""

from __future__ import annotations

import os
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
    pipeline,
    reports,
    scoring,
    spec,
)


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
        Base.metadata.create_all(engine)
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
