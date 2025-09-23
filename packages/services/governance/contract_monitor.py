from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import desc
from sqlalchemy.orm import Session

from packages.database.models.governance import APIContract, RiskEvent


@dataclass
class SchemaRecord:
    org_id: str
    provider: str  # cj|amazon|sheets|internal
    version: str
    schema: Dict[str, Any]


class ContractMonitor:
    """
    Page-only Contract Monitor.

    - Computes a stable schema hash from a schema dict
    - Stores entries in `api_contract`
    - On hash change (drift), also writes a `risk_event` with signal 'schema_drift'
    """

    @staticmethod
    def compute_hash(schema: Dict[str, Any]) -> str:
        # Stable hash via JSON dumps with sorted keys and no whitespace variance
        payload = json.dumps(schema, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record(self, session: Session, rec: SchemaRecord) -> APIContract:
        now = datetime.utcnow()
        schema_hash = self.compute_hash(rec.schema)

        # Fetch last stored for org+provider
        last = (
            session.query(APIContract)
            .filter(APIContract.org_id == rec.org_id, APIContract.provider == rec.provider)
            .order_by(desc(APIContract.id))
            .first()
        )

        drifted = (last is None) or (last.schema_hash != schema_hash)

        row = APIContract(
            org_id=rec.org_id,
            provider=rec.provider,
            version=rec.version,
            schema_hash=schema_hash,
            schema=json.dumps(rec.schema, sort_keys=True),
            created_at=now,
        )
        session.add(row)

        if drifted and last is not None:
            # Only flag risk when there's a prior baseline and the hash changed
            session.add(
                RiskEvent(
                    org_id=rec.org_id,
                    source=f"contract_monitor:{rec.provider}",
                    signal="schema_drift",
                    level="high",
                    value=None,
                    meta=json.dumps(
                        {
                            "prev_hash": last.schema_hash,
                            "new_hash": schema_hash,
                            "provider": rec.provider,
                        }
                    ),
                    timestamp=now,
                    created_at=now,
                )
            )

        session.commit()
        return row
