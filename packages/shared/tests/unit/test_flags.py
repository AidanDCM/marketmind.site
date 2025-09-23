"""Unit tests for the feature flags module."""

import os
from unittest.mock import patch

import pytest

from packages.shared.config.flags import (
    ChannelMode,
    FeatureFlag,
    FeatureFlags,
    channel_mode_override,
    feature_flag_override,
    get_channel_mode,
    get_flags,
    is_feature_enabled,
)
from packages.shared.config.schema import AppSettings


def test_feature_flag_enum():
    """Test the FeatureFlag enum values."""
    assert FeatureFlag.SIMULATION_MODE == "simulation_mode"
    assert FeatureFlag.PRICING_ENGINE == "pricing_engine"
    assert FeatureFlag.ORDER_SYNC == "order_sync"
    assert FeatureFlag.INVENTORY_SYNC == "inventory_sync"
    assert FeatureFlag.ANALYTICS == "analytics"


def test_channel_mode_enum():
    """Test the ChannelMode enum values."""
    assert ChannelMode.NORMAL == "normal"
    assert ChannelMode.MAINTENANCE == "maintenance"
    assert ChannelMode.DEGRADED == "degraded"


def test_feature_flags_defaults():
    """Test FeatureFlags with default values."""
    flags = FeatureFlags()
    assert flags.simulation_mode is False
    assert flags.pricing_engine is True
    assert flags.order_sync is True
    assert flags.inventory_sync is True
    assert flags.analytics is True


def test_feature_flags_from_dict():
    """Test creating FeatureFlags from a dictionary."""
    flags_dict = {
        "simulation_mode": True,
        "pricing_engine": False,
        "order_sync": False,
        "inventory_sync": True,
        "analytics": False,
    }
    flags = FeatureFlags(**flags_dict)

    assert flags.simulation_mode is True
    assert flags.pricing_engine is False
    assert flags.order_sync is False
    assert flags.inventory_sync is True
    assert flags.analytics is False


def test_is_feature_enabled():
    """Test the is_feature_enabled function."""
    flags = FeatureFlags(simulation_mode=True, pricing_engine=False)

    # Test with flag names
    assert is_feature_enabled(FeatureFlag.SIMULATION_MODE, flags) is True
    assert is_feature_enabled(FeatureFlag.PRICING_ENGINE, flags) is False

    # Test with string flag names
    assert is_feature_enabled("simulation_mode", flags) is True
    assert is_feature_enabled("pricing_engine", flags) is False

    # Test with non-existent flag (should return False)
    assert is_feature_enabled("nonexistent_flag", flags) is False


def test_get_channel_mode():
    """Test the get_channel_mode function."""
    # Default channel mode is NORMAL
    assert get_channel_mode() == ChannelMode.NORMAL

    # Test with custom flags
    flags = FeatureFlags(channel_mode=ChannelMode.MAINTENANCE)
    assert get_channel_mode(flags) == ChannelMode.MAINTENANCE


def test_feature_flag_override():
    """Test the feature_flag_override context manager."""
    original_flags = FeatureFlags(simulation_mode=False, pricing_engine=True)

    # Override a single flag
    with feature_flag_override(FeatureFlag.SIMULATION_MODE, True, original_flags):
        assert is_feature_enabled(FeatureFlag.SIMULATION_MODE, original_flags) is True
        assert is_feature_enabled(FeatureFlag.PRICING_ENGINE, original_flags) is True

    # Original flags should be restored
    assert is_feature_enabled(FeatureFlag.SIMULATION_MODE, original_flags) is False

    # Override multiple flags
    with feature_flag_override(
        {FeatureFlag.SIMULATION_MODE: True, FeatureFlag.PRICING_ENGINE: False}, original_flags
    ):
        assert is_feature_enabled(FeatureFlag.SIMULATION_MODE, original_flags) is True
        assert is_feature_enabled(FeatureFlag.PRICING_ENGINE, original_flags) is False

    # Original flags should be restored
    assert is_feature_enabled(FeatureFlag.SIMULATION_MODE, original_flags) is False
    assert is_feature_enabled(FeatureFlag.PRICING_ENGINE, original_flags) is True


def test_channel_mode_override():
    """Test the channel_mode_override context manager."""
    original_flags = FeatureFlags()

    # Override channel mode
    with channel_mode_override(ChannelMode.MAINTENANCE, original_flags):
        assert get_channel_mode(original_flags) == ChannelMode.MAINTENANCE

    # Original channel mode should be restored
    assert get_channel_mode(original_flags) == ChannelMode.NORMAL


def test_get_flags():
    """Test the get_flags function."""
    # Default flags
    flags1 = get_flags()
    flags2 = get_flags()

    # Should return the same instance (singleton)
    assert flags1 is flags2

    # Should have default values
    assert flags1.simulation_mode is False
    assert flags1.pricing_engine is True


def test_feature_flags_from_settings():
    """Test creating FeatureFlags from AppSettings."""
    settings = AppSettings(
        flags={"simulation_mode": True, "pricing_engine": False, "channel_mode": "maintenance"}
    )

    flags = FeatureFlags.from_settings(settings)

    assert flags.simulation_mode is True
    assert flags.pricing_engine is False
    assert flags.channel_mode == "maintenance"


def test_feature_flag_validation():
    """Test validation of feature flag values."""
    # Valid values
    FeatureFlags(simulation_mode=True, pricing_engine=False)

    # Invalid channel mode should raise ValueError
    with pytest.raises(ValueError):
        FeatureFlags(channel_mode="invalid_mode")


@patch.dict(
    os.environ,
    {"FEATURE_SIMULATION_MODE": "1", "FEATURE_PRICING_ENGINE": "0", "CHANNEL_MODE": "degraded"},
)
def test_feature_flags_from_env():
    """Test loading feature flags from environment variables."""
    flags = FeatureFlags()

    assert flags.simulation_mode is True
    assert flags.pricing_engine is False
    assert flags.channel_mode == "degraded"
