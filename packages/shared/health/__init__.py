"""
Health check functionality for the MarketMind application.

This package provides health check endpoints and utilities to monitor
the status of the application and its dependencies.

Example usage:

    from packages.shared.health.probes import get_health

    # Get health status
    health_status = get_health()
    print(health_status)
"""

from .probes import (
    HealthChecker,
    HealthCheckResult,
    get_all_health_checks,
    get_health,
    get_health_summary,
)

__all__ = [
    "HealthCheckResult",
    "HealthChecker",
    "get_health",
    "get_all_health_checks",
    "get_health_summary",
]
