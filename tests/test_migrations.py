"""Slice 30: Alembic migration chain smoke tests.

These tests run against a temporary SQLite file (not in-memory) because
Alembic's migration state table (alembic_version) must be persisted between
upgrade/downgrade calls.
"""

from __future__ import annotations

import pathlib

import pytest
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, inspect, text

from alembic import command as alembic_cmd

_ALEMBIC_INI = pathlib.Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture
def alembic_cfg(tmp_path: pathlib.Path) -> AlembicConfig:
    db_path = tmp_path / "test.db"
    cfg = AlembicConfig(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


@pytest.fixture
def db_url(alembic_cfg: AlembicConfig) -> str:
    return alembic_cfg.get_main_option("sqlalchemy.url")  # type: ignore[return-value]


def test_upgrade_head_creates_all_tables(alembic_cfg, db_url):
    """upgrade head should produce all expected tables."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    assert "approvals" in tables
    assert "experiments" in tables
    assert "experiment_snapshots" in tables
    assert "events" in tables
    assert "import_batches" in tables
    assert "alembic_version" in tables


def test_upgrade_is_idempotent(alembic_cfg, db_url):
    """Running upgrade head twice must not error."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    alembic_cmd.upgrade(alembic_cfg, "head")
    engine = create_engine(db_url)
    assert "import_batches" in inspect(engine).get_table_names()


def test_downgrade_0001_removes_import_batches(alembic_cfg, db_url):
    """Downgrading to 0001 should drop import_batches but keep the rest."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    alembic_cmd.downgrade(alembic_cfg, "0001")
    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    assert "import_batches" not in tables
    assert "approvals" in tables
    assert "events" in tables


def test_downgrade_base_drops_all(alembic_cfg, db_url):
    """Downgrading to base should remove all application tables."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    alembic_cmd.downgrade(alembic_cfg, "base")
    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    # Only the Alembic bookkeeping table should remain (if any)
    app_tables = {"approvals", "experiments", "experiment_snapshots", "events", "import_batches"}
    assert app_tables.isdisjoint(tables)


def test_round_trip_upgrade_downgrade_upgrade(alembic_cfg, db_url):
    """Full up → down → up must leave the schema at head with no errors."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    alembic_cmd.downgrade(alembic_cfg, "base")
    alembic_cmd.upgrade(alembic_cfg, "head")
    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    assert "import_batches" in tables
    assert "approvals" in tables


def test_import_batches_columns(alembic_cfg, db_url):
    """The import_batches table should have the expected columns."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    engine = create_engine(db_url)
    cols = {c["name"] for c in inspect(engine).get_columns("import_batches")}
    expected = {"id", "source", "pulled_at", "total_rows", "ok_count", "review_count", "rows_json"}
    assert cols >= expected


def test_current_version_is_head(alembic_cfg, db_url):
    """After upgrade head, alembic_version should record 0002."""
    alembic_cmd.upgrade(alembic_cfg, "head")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
    assert row is not None
    assert row[0] == "0002"
