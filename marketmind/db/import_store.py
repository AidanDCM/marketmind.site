"""Slice 29: persistence layer for import batch history."""

from __future__ import annotations

import json

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from ..schemas import ImportResult
from .models import ImportBatchRow


def save_import(engine: Engine, result: ImportResult) -> int:
    """Persist an ImportResult and return the new batch id."""
    rows_json = json.dumps([r.data for r in result.ok_rows])
    with Session(engine) as session:
        row = ImportBatchRow(
            source=result.source,
            total_rows=result.total_rows,
            ok_count=len(result.ok_rows),
            review_count=len(result.review_rows),
            rows_json=rows_json,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def list_imports(engine: Engine, source: str | None = None, limit: int = 50) -> list[dict]:
    """Return recent import batches, newest first. Optionally filter by source."""
    with Session(engine) as session:
        stmt = select(ImportBatchRow).order_by(ImportBatchRow.id.desc()).limit(limit)
        if source:
            stmt = stmt.where(ImportBatchRow.source == source)
        rows = session.scalars(stmt).all()
        return [
            {
                "id": r.id,
                "source": r.source,
                "pulled_at": r.pulled_at,
                "total_rows": r.total_rows,
                "ok_count": r.ok_count,
                "review_count": r.review_count,
            }
            for r in rows
        ]


def get_import(engine: Engine, batch_id: int) -> dict | None:
    """Return one batch including its row data, or None if not found."""
    with Session(engine) as session:
        row = session.get(ImportBatchRow, batch_id)
        if row is None:
            return None
        return {
            "id": row.id,
            "source": row.source,
            "pulled_at": row.pulled_at,
            "total_rows": row.total_rows,
            "ok_count": row.ok_count,
            "review_count": row.review_count,
            "rows": json.loads(row.rows_json),
        }
