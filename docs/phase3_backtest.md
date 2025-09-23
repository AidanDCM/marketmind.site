# Phase 3 Backtest Guide

This document describes how to run and validate the Phase 3 backtest for MarketMind to ensure the system is stable before Phase 4.

## Prerequisites
- Python 3.9+
- Virtual environment with dependencies installed
- SQLite (dev default) or configured Postgres

## One-time Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r infra/docker/requirements-api.txt
pip install -r infra/docker/requirements-worker.txt
pip install -r requirements-dev.txt
```

## Run the Phase 3 Backtest
```bash
make phase3-backtest
```
This performs:
- Secrets scan with gitleaks
- Python dependency audit with pip-audit
- Alembic migrations to head
- Sanity counts from the local DB
- Internal probes (Phase 2 suite as smoke)
- CHANGELOG entry append on success

Expected: all checks pass, with overall tests/coverage validated separately.

## Tooling and Type Checking
- Linting: `make lint` (Ruff)
- Formatting: `make format` (Black + Ruff format)
- Type checking: `make type-check` (mypy)

Note: legacy models in `packages/models/` are excluded from lint/type checks. Active SQLAlchemy 2.0 models are under `packages/database/models/`.

## SQLAlchemy 2.0 Migration
- Active models use `Mapped[]` annotations and `mapped_column()` with typed relationships.
- Association tables (e.g., `product_category.py`) use `Table` with `Column`, which is acceptable for pure table constructs.

## Dependency Security
- pip-audit is run deterministically against:
  - `requirements-dev.txt`
  - `infra/docker/requirements-api.txt`
  - `infra/docker/requirements-worker.txt`
- Current state: FastAPI is pinned to `0.116.1` and Starlette to `0.47.2`, which remediates prior Starlette advisories. The temporary ignore has been removed from `scripts/ci/security_checks.sh`. If pip-audit flags issues, review and bump pins accordingly.

## Troubleshooting
- If pip-audit fails due to resolver conflicts, verify FastAPI↔Starlette pins in `infra/docker/requirements-api.txt`.
- If migrations fail, ensure Alembic is using the active Base from `packages/database/models/`.

## Final Validation
Run:
```bash
make format && make lint && make type-check && make phase3-backtest
```
All steps should pass cleanly before proceeding to Phase 4.
