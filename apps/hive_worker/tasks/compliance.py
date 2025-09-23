from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from celery import shared_task
from sqlalchemy.orm import Session

from packages.database.models import CompliancePack, RestrictedCategory, RestrictedTerm
from packages.shared.db import get_session_factory
from packages.shared.sheets import SheetsClient


def _parse_pack_source(source_uri: str) -> dict:
    # Simple parser: if source_uri starts with json://, parse embedded JSON
    if source_uri and source_uri.startswith("json://"):
        try:
            return json.loads(source_uri[len("json://") :])
        except Exception:
            return {"terms": [], "categories": []}
    # TODO: support s3://, gs://, http(s):// in Phase 12
    return {"terms": [], "categories": []}


@shared_task(name="apps.hive_worker.tasks.compliance.compile_pack", queue="q.backfill")
def compile_pack(pack_id: int, source_uri: Optional[str] = None) -> dict:
    """Compile a policy pack into DB tables from its source."""
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    sheets = SheetsClient()
    try:
        pack = db.query(CompliancePack).filter(CompliancePack.id == pack_id).one_or_none()
        if not pack:
            return {"ok": False, "error": "pack_not_found"}

        data = _parse_pack_source(source_uri or pack.source_uri)
        terms = data.get("terms", [])
        cats = data.get("categories", [])

        # wipe existing for idempotency
        db.query(RestrictedTerm).filter(RestrictedTerm.pack_id == pack.id).delete()
        db.query(RestrictedCategory).filter(RestrictedCategory.pack_id == pack.id).delete()

        for t in terms:
            db.add(
                RestrictedTerm(
                    pack_id=pack.id,
                    term=str(t.get("term", "")).strip(),
                    kind=t.get("kind", "term"),
                    locale=t.get("locale", "en_US"),
                    severity=t.get("severity", "warn"),
                    notes=t.get("notes", ""),
                )
            )
        for c in cats:
            db.add(
                RestrictedCategory(
                    pack_id=pack.id,
                    channel=c.get("channel", ""),
                    code=c.get("code", ""),
                    label=c.get("label", ""),
                    notes=c.get("notes", ""),
                )
            )

        pack.updated_at = datetime.utcnow()
        db.commit()

        # Sheets echo (best-effort)
        try:
            headers = [
                "timestamp",
                "pack_id",
                "name",
                "version",
                "terms_count",
                "categories_count",
            ]
            row = [
                datetime.utcnow().isoformat(),
                pack.id,
                pack.name,
                pack.version,
                len(terms),
                len(cats),
            ]
            sheets.append_rows("Compliance Packs", headers, [row])
        except Exception:
            pass

        return {"ok": True, "pack_id": pack.id, "terms": len(terms), "categories": len(cats)}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@shared_task(name="apps.hive_worker.tasks.compliance.reload_enabled_packs", queue="q.backfill")
def reload_enabled_packs() -> dict:
    """Compile all enabled compliance packs. Idempotent and safe to run periodically."""
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    try:
        packs = db.query(CompliancePack).filter(CompliancePack.enabled == True).all()  # noqa: E712
        results = []
        for p in packs:
            try:
                res = compile_pack(p.id, p.source_uri)
            except Exception as e:  # pragma: no cover - defensive
                res = {"ok": False, "error": str(e), "pack_id": p.id}
            results.append(res)
        return {"ok": True, "count": len(results), "results": results}
    finally:
        db.close()
