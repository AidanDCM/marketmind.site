from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

DEFAULTS = {
    "min_net_margin_pct": 12.0,
    "max_undercut_step": 0.05,  # 5%
    "respect_map": True,
    "free_shipping_enabled": True,
    "platform_fee_pct": 0.15,
    "return_reserve_pct": 0.02,
    "est_shipping_flat": 4.00,
}


@dataclass
class Guardrails:
    min_net_margin_pct: float = DEFAULTS["min_net_margin_pct"]
    max_undercut_step: float = DEFAULTS["max_undercut_step"]
    respect_map: bool = DEFAULTS["respect_map"]
    free_shipping_enabled: bool = DEFAULTS["free_shipping_enabled"]
    platform_fee_pct: float = DEFAULTS["platform_fee_pct"]
    return_reserve_pct: float = DEFAULTS["return_reserve_pct"]
    est_shipping_flat: float = DEFAULTS["est_shipping_flat"]


def landed_cost(
    supplier_cost: float,
    shipping_flat: float,
    platform_fee_pct: float,
    return_reserve_pct: float,
    target_price: Optional[float] = None,
) -> float:
    # If a target price is provided, fees are applied to target price; otherwise approximate against supplier cost
    fee_base = target_price if target_price is not None else supplier_cost
    fees = fee_base * platform_fee_pct
    reserve = fee_base * return_reserve_pct
    return supplier_cost + shipping_flat + fees + reserve


def psych_price(price: float) -> float:
    # 9-ending rule: round down to nearest .99
    cents = math.floor(price) + 0.99
    if cents > price:
        # ensure we don't increase price
        cents = math.floor(price - 0.01) + 0.99
    return round(cents, 2)


def propose_price(
    best_comp_price: Optional[float],
    supplier_cost: float,
    guard: Guardrails,
    map_price: Optional[float] = None,
) -> Dict[str, Any]:
    # Start from competitor undercut if available
    base = None
    if best_comp_price is not None:
        base = best_comp_price * (1.0 - guard.max_undercut_step)
    else:
        # Fallback: cost plus margin baseline
        base = supplier_cost * (1.0 + (guard.min_net_margin_pct / 100.0)) + guard.est_shipping_flat

    # Apply MAP
    if guard.respect_map and map_price is not None:
        base = max(base, map_price)

    # Apply landed cost model to ensure margin floor
    lc = landed_cost(
        supplier_cost,
        guard.est_shipping_flat if guard.free_shipping_enabled else 0.0,
        guard.platform_fee_pct,
        guard.return_reserve_pct,
        target_price=base,
    )
    # Ensure net margin meets minimum
    margin_pct = 0.0
    if base > 0:
        margin_pct = max(0.0, (base - lc) / base * 100.0)
    if margin_pct < guard.min_net_margin_pct:
        # raise price to meet margin
        # Solve for price p: (p - landed_cost(p)) / p = min_margin
        # landed_cost(p) = supplier + ship + p*fee + p*reserve
        # net = p - (supplier + ship) - p*(fee+reserve) = p*(1 - fee - reserve) - (supplier+ship)
        # net/p = (1 - fee - reserve) - (supplier+ship)/p
        # We want net/p = min_margin
        m = guard.min_net_margin_pct / 100.0
        k = 1.0 - guard.platform_fee_pct - guard.return_reserve_pct
        numer = supplier_cost + (guard.est_shipping_flat if guard.free_shipping_enabled else 0.0)
        # p such that (p*k - numer)/p = m => k - numer/p = m => numer/p = k - m => p = numer / (k - m)
        denom = k - m
        if denom <= 0:
            base = supplier_cost * 2.0  # worst-case safe fallback
        else:
            base = max(base, numer / denom)
        # recompute margin
        lc = landed_cost(
            supplier_cost,
            guard.est_shipping_flat if guard.free_shipping_enabled else 0.0,
            guard.platform_fee_pct,
            guard.return_reserve_pct,
            target_price=base,
        )
        margin_pct = max(0.0, (base - lc) / base * 100.0)

    # Psychological price
    proposed = psych_price(base)
    # Ensure psych adjustment did not break margin floor
    lc2 = landed_cost(
        supplier_cost,
        guard.est_shipping_flat if guard.free_shipping_enabled else 0.0,
        guard.platform_fee_pct,
        guard.return_reserve_pct,
        target_price=proposed,
    )
    margin_pct2 = max(0.0, (proposed - lc2) / proposed * 100.0) if proposed > 0 else 0.0
    if margin_pct2 < guard.min_net_margin_pct:
        # bump by 1 dollar to restore margin, then re-apply psych pricing
        proposed = psych_price(proposed + 1.0)
        lc2 = landed_cost(
            supplier_cost,
            guard.est_shipping_flat if guard.free_shipping_enabled else 0.0,
            guard.platform_fee_pct,
            guard.return_reserve_pct,
            target_price=proposed,
        )
        margin_pct2 = max(0.0, (proposed - lc2) / proposed * 100.0) if proposed > 0 else 0.0

    return {
        "proposed_price": round(proposed, 2),
        "margin_pct": round(margin_pct2, 2),
        "landed_cost": round(lc2, 2),
        "inputs": {
            "best_comp_price": best_comp_price,
            "supplier_cost": supplier_cost,
            "map_price": map_price,
            "guardrails": guard.__dict__,
        },
    }
