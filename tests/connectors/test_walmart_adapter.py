"""
Smoke tests for the Walmart adapter stub.
"""

from unittest.mock import patch

import pytest

from packages.connectors.channels.walmart import WalmartAdapter
from packages.connectors.shared.exceptions import ChannelAuthError


@pytest.fixture
def walmart_adapter():
    with patch("requests.Session"):
        adapter = WalmartAdapter(
            client_id="client",
            client_secret="secret",
            sandbox=True,
        )
        yield adapter


def test_authenticate_success(walmart_adapter):
    assert walmart_adapter.authenticate() is True
    assert walmart_adapter._token is not None


def test_authenticate_missing_credentials():
    with patch("requests.Session"):
        adapter = WalmartAdapter(client_id="", client_secret="")
        with pytest.raises(ChannelAuthError):
            adapter.authenticate()


def test_health_ok(walmart_adapter):
    res = walmart_adapter.health()
    assert res.get("ok") is True
    assert res.get("name") == "walmart"


def test_idempotent_update_listing(walmart_adapter):
    # Call twice; decorator should allow idempotent behavior without errors
    walmart_adapter.update_listing("L-1", {"title": "x"})
    walmart_adapter.update_listing("L-1", {"title": "x"})


def test_idempotent_publish_price(walmart_adapter):
    walmart_adapter.publish_price("L-1", 12345)
    walmart_adapter.publish_price("L-1", 12345)


def test_retry_backoff_on_request(walmart_adapter):
    # Ensure authenticate provides a token
    walmart_adapter.authenticate()

    # Simulate two transient failures then success
    with patch.object(walmart_adapter, "session") as mock_session:

        class Resp:
            status_code = 200
            content = b"{}"

            def json(self):
                return {}

        import requests

        mock_session.request.side_effect = [
            requests.exceptions.RequestException("net down"),
            requests.exceptions.RequestException("timeout"),
            Resp(),
        ]

        data = walmart_adapter._make_request("GET", "/ping")
        assert isinstance(data, dict)
        assert mock_session.request.call_count == 3
