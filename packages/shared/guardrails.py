import json
import os

from pydantic import BaseModel


class Guardrails(BaseModel):
    min_net_margin_pct: float = 18.0
    blitz_min_net_margin_pct: float = 10.0
    blitz_enabled: bool = False
    blitz_max_days: int = 14
    max_undercut_step: float = 0.25
    respect_map: bool = True
    free_shipping_enabled: bool = True


_path = os.getenv("GUARDRAILS_PATH", "/data/guardrails.json")


def load_guardrails() -> Guardrails:
    try:
        with open(_path, "r") as f:
            return Guardrails(**json.load(f))
    except Exception:
        return Guardrails()


def save_guardrails(g: Guardrails):
    os.makedirs(os.path.dirname(_path), exist_ok=True)
    with open(_path, "w") as f:
        json.dump(g.model_dump(), f, indent=2)
