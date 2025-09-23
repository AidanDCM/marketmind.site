"""Ledger package for maintaining financial records."""

from typing import Optional

from .config import LedgerSettings, settings
from .service import LedgerService, ledger_service


def init_ledger(config: Optional[LedgerSettings] = None) -> LedgerService:
    """Initialize the ledger service with the given configuration.

    Args:
        config: Optional configuration. If not provided, uses default settings.

    Returns:
        Initialized LedgerService instance.
    """
    global ledger_service

    if config is not None:
        ledger_service.config = config

    return ledger_service


__all__ = ["LedgerService", "ledger_service", "init_ledger", "settings", "LedgerSettings"]
