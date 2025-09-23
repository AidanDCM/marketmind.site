import importlib
import os
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def clear_settings_cache():
    # Ensure settings are reloaded fresh for each test case
    from packages.shared.config import loader

    loader.get_settings.cache_clear()
    yield
    loader.get_settings.cache_clear()


def test_health_probes_without_prometheus_client(monkeypatch):
    # Minimal env to avoid config fatal errors
    os.environ["APP_ENV"] = "development"
    os.environ["DB_URL"] = os.getenv("DB_URL", "sqlite:///./dev.db")

    # Install a dummy prometheus_client without Histogram symbol to force optional path
    sys.modules["prometheus_client"] = types.SimpleNamespace()

    # Reload probes to re-evaluate optional import
    probes = importlib.import_module("packages.shared.health.probes")
    importlib.reload(probes)

    checker = probes.HealthChecker()
    results = checker.check_all()

    # Should return a dict of HealthCheckResult without raising even if Prometheus is missing
    assert isinstance(results, dict)
    assert "config" in results
    assert hasattr(results["config"], "status")

    # Ensure get_all_health_checks also works
    all_checks = probes.get_all_health_checks()
    assert isinstance(all_checks, dict)
    assert "checks" in all_checks
    assert isinstance(all_checks["checks"], dict)
