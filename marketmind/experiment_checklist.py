"""Experiment scale-readiness checklist for MarketMind.

Adapted from Parts-and-Pieces `parts/python/checklist_gate`.

Before an experiment receives a SCALE_REQUIRES_APPROVAL ruling and a human
approves scaling, the system checks a set of conditions. This module defines
those conditions and exposes a function that returns the checklist state for
any experiment + latest snapshot combination.

Use this via `GET /experiment/{id}/checklist` to get a structured readiness
report before submitting a scale approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ChecklistItem:
    item_id: str
    description: str
    required: bool = True
    passed: bool = False
    evidence: str = ""
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def build_experiment_scale_checklist(
    *,
    experiment_id: str,
    product_name: str,
    status: str,
    qualified_visits: int,
    orders: int,
    total_ad_spend: float,
    actual_cac: float | None,
    break_even_cac: float,
    consecutive_losing_periods: int,
    latest_snapshot_date: str | None,
    has_approval: bool = False,
) -> list[ChecklistItem]:
    """Return a checklist of conditions that must pass before scaling an experiment.

    All required items must pass before the system allows a scale action
    to proceed to the approval gate.
    """
    items: list[ChecklistItem] = []

    # 1. Experiment is active
    active = status == "active"
    items.append(ChecklistItem(
        item_id="status_active",
        description="Experiment status is active",
        required=True,
        passed=active,
        evidence=f"status={status}",
    ))

    # 2. Minimum traffic observed
    min_visits = 100
    items.append(ChecklistItem(
        item_id="min_traffic",
        description=f"At least {min_visits} qualified visits recorded",
        required=True,
        passed=qualified_visits >= min_visits,
        evidence=f"qualified_visits={qualified_visits}",
    ))

    # 3. Minimum orders placed
    min_orders = 5
    items.append(ChecklistItem(
        item_id="min_orders",
        description=f"At least {min_orders} orders recorded",
        required=True,
        passed=orders >= min_orders,
        evidence=f"orders={orders}",
    ))

    # 4. CAC is at or below break-even
    cac_ok = actual_cac is not None and actual_cac <= break_even_cac
    items.append(ChecklistItem(
        item_id="cac_at_or_below_break_even",
        description="Actual CAC is at or below break-even CAC",
        required=True,
        passed=cac_ok,
        evidence=(
            f"actual_cac=${actual_cac:.2f}, break_even_cac=${break_even_cac:.2f}"
            if actual_cac is not None
            else "no snapshot data"
        ),
    ))

    # 5. No consecutive losing periods
    items.append(ChecklistItem(
        item_id="no_consecutive_losses",
        description="Zero consecutive losing periods",
        required=True,
        passed=consecutive_losing_periods == 0,
        evidence=f"consecutive_losing_periods={consecutive_losing_periods}",
    ))

    # 6. Recent snapshot exists
    items.append(ChecklistItem(
        item_id="recent_snapshot",
        description="At least one snapshot has been recorded",
        required=True,
        passed=latest_snapshot_date is not None,
        evidence=f"latest_snapshot_date={latest_snapshot_date or 'none'}",
    ))

    # 7. Spend has been committed (prevents scaling on zero-spend flukes)
    min_spend = 50.0
    items.append(ChecklistItem(
        item_id="minimum_spend_committed",
        description=f"At least ${min_spend:.0f} ad spend recorded",
        required=True,
        passed=total_ad_spend >= min_spend,
        evidence=f"total_ad_spend=${total_ad_spend:.2f}",
    ))

    # 8. Human approval obtained (advisory — informational, not a gate)
    items.append(ChecklistItem(
        item_id="approval_obtained",
        description="Scale action has an approved ApprovalRow",
        required=False,
        passed=has_approval,
        evidence="approval_status=approved" if has_approval else "no approval yet",
    ))

    return items


def checklist_ready(items: list[ChecklistItem]) -> bool:
    """Return True only if every required checklist item passed."""
    return all((not item.required) or item.passed for item in items)


def checklist_blockers(items: list[ChecklistItem]) -> list[str]:
    """Return descriptions of required items that have not passed."""
    return [item.description for item in items if item.required and not item.passed]
