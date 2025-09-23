"""Exceptions and playbooks scaffold for orders.

Defines exception kinds and skeleton handlers that will later integrate with
sheets echo, audit logs, and channel/customer messaging.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ExceptionKind(str, Enum):
    OOS = "OOS"
    ADDRESS_FAIL = "ADDRESS_FAIL"
    PARTIAL = "PARTIAL"
    DELAY = "DELAY"
    CANCEL = "CANCEL"
    REFUND = "REFUND"
    RETURN = "RETURN"


@dataclass
class ExceptionTicket:
    order_id: int
    kind: ExceptionKind
    note: Optional[str] = None
    state: str = "OPEN"


class ExceptionsService:
    def __init__(self):
        pass

    def open(
        self, order_id: int, kind: ExceptionKind, note: Optional[str] = None
    ) -> ExceptionTicket:
        # TODO: persist to DB + audit log + optional Sheets echo
        return ExceptionTicket(order_id=order_id, kind=kind, note=note)

    def resolve(self, ticket: ExceptionTicket, resolution: str) -> ExceptionTicket:
        # TODO: persist resolution
        ticket.state = "RESOLVED"
        return ticket
