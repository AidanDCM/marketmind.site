from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml
from sqlalchemy.orm import Session

from packages.database.models.governance import GovernanceDecision


@dataclass
class Condition:
    field: str
    op: str
    value: Any


@dataclass
class Rule:
    name: str
    action: str  # allow|deny|warn
    conditions: List[Condition]
    scope: str = "global"
    priority: int = 100


class PolicyEngine:
    """Observe-only policy engine that evaluates simple YAML rules.

    Rule format (YAML):
    - name: "Minimum Margin"
      action: "warn"   # allow|deny|warn
      priority: 50
      scope: "pricing"
      match:
        all:
          - field: "pricing.margin_pct"
            op: ">="
            value: 10
    """

    def __init__(
        self, db: Session, rules: Optional[List[Rule]] = None, rules_path: Optional[str] = None
    ) -> None:
        self.db = db
        self.rules: List[Rule] = rules or []
        self.rules_path = rules_path or os.path.join("config", "governance", "policies.yaml")
        if not self.rules:
            self._load_rules_from_yaml()

    def _load_rules_from_yaml(self) -> None:
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or []
            else:
                data = []
        except Exception:
            data = []
        self.rules = []
        for item in data:
            conds = []
            for c in item.get("match", {}).get("all", []) or []:
                conds.append(Condition(field=c.get("field"), op=c.get("op"), value=c.get("value")))
            self.rules.append(
                Rule(
                    name=item.get("name", "unnamed"),
                    action=item.get("action", "warn"),
                    priority=int(item.get("priority", 100)),
                    scope=item.get("scope", "global"),
                    conditions=conds,
                )
            )
        # Sort by priority ascending (lower runs first)
        self.rules.sort(key=lambda r: r.priority)

    @staticmethod
    def _get_by_path(ctx: Dict[str, Any], path: str) -> Any:
        node: Any = ctx
        for part in path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node

    @staticmethod
    def _eval_op(lhs: Any, op: str, rhs: Any) -> bool:
        try:
            if op == "==":
                return lhs == rhs
            if op == "!=":
                return lhs != rhs
            if op == ">":
                return lhs is not None and rhs is not None and lhs > rhs
            if op == ">=":
                return lhs is not None and rhs is not None and lhs >= rhs
            if op == "<":
                return lhs is not None and rhs is not None and lhs < rhs
            if op == "<=":
                return lhs is not None and rhs is not None and lhs <= rhs
            if op == "in":
                return lhs in (rhs or [])
            if op == "contains":
                return (rhs in lhs) if hasattr(lhs, "__contains__") else False
        except Exception:
            return False
        return False

    def evaluate(
        self, *, org_id: str, entity_type: str, entity_id: str, context: Dict[str, Any]
    ) -> GovernanceDecision:
        hits: List[str] = []
        for rule in self.rules:
            if not rule.conditions:
                continue
            ok = True
            for cond in rule.conditions:
                lhs = self._get_by_path(context, cond.field)
                if not self._eval_op(lhs, cond.op, cond.value):
                    ok = False
                    break
            if ok:
                hits.append(rule.name)
        # Observe-only: decision is simulate; confidence 0.0
        decision = GovernanceDecision(
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            policy_hits=json.dumps(hits),
            risk_score=0.0,
            decision="simulate",
            confidence=0.0,
            context=json.dumps({"scope": "observe", "n_rules": len(self.rules)}),
        )
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision
