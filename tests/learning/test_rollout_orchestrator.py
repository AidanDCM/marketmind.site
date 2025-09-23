"""Unit tests for learning rollout orchestration functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from apps.hive_worker.tasks.learning import promote_rollout_task


class TestRolloutOrchestrator:
    """Test suite for rollout promotion and orchestration."""

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_promote_rollout_success(self, mock_session_local):
        """Test successful rollout promotion."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        # Mock existing rollout in shadow phase
        mock_rollout = Mock()
        mock_rollout.id = 1
        mock_rollout.model_version_id = 123
        mock_rollout.brain_id = "pricing"
        mock_rollout.phase = "shadow"
        mock_rollout.percent = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rollout

        # Mock no drift reports or good benchmarks
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = promote_rollout_task(1, "canary", 25)

        assert result["ok"] is True
        assert result["rollout_id"] == 1
        assert result["phase"] == "canary"
        assert result["percent"] == 25
        assert result["model_version_id"] == 123
        assert result["brain_id"] == "pricing"

        # Verify rollout was updated
        assert mock_rollout.phase == "canary"
        assert mock_rollout.percent == 25
        mock_db.commit.assert_called()

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_promote_rollout_blocked_by_drift(self, mock_session_local):
        """Test rollout promotion blocked by high-severity drift reports."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_rollout = Mock()
        mock_rollout.phase = "shadow"
        mock_rollout.model_version_id = 123
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rollout

        # Mock high-severity drift reports
        mock_db.query.return_value.filter.return_value.count.return_value = 2

        result = promote_rollout_task(1, "canary", 25)

        assert result["ok"] is False
        assert "Blocked by 2 high-severity drift reports" in result["error"]

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_promote_rollout_blocked_by_low_benchmark(self, mock_session_local):
        """Test rollout promotion blocked by low benchmark scores."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_rollout = Mock()
        mock_rollout.phase = "shadow"
        mock_rollout.model_version_id = 123
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rollout

        # Mock no drift reports but low benchmark scores
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        mock_benchmark1 = Mock()
        mock_benchmark1.score = 0.6
        mock_benchmark2 = Mock()
        mock_benchmark2.score = 0.5
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_benchmark1,
            mock_benchmark2,
        ]

        result = promote_rollout_task(1, "canary", 25)

        assert result["ok"] is False
        assert "Benchmark score 0.550 below threshold 0.700" in result["error"]

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_promote_rollout_invalid_phase_transition(self, mock_session_local):
        """Test rollout promotion with invalid phase transition."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_rollout = Mock()
        mock_rollout.phase = "production"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rollout

        result = promote_rollout_task(1, "canary", 25)

        assert result["ok"] is False
        assert "Invalid phase transition" in result["error"]

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_promote_rollout_rollback_to_shadow(self, mock_session_local):
        """Test rollout rollback to shadow phase is always allowed."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_rollout = Mock()
        mock_rollout.id = 1
        mock_rollout.model_version_id = 123
        mock_rollout.brain_id = "pricing"
        mock_rollout.phase = "production"
        mock_rollout.percent = 100

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rollout

        result = promote_rollout_task(1, "shadow", 0)

        assert result["ok"] is True
        assert result["phase"] == "shadow"
        assert result["percent"] == 0

        # Verify rollout was updated to shadow
        assert mock_rollout.phase == "shadow"
        assert mock_rollout.percent == 0

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_promote_rollout_not_found(self, mock_session_local):
        """Test rollout promotion when rollout doesn't exist."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = promote_rollout_task(999, "canary", 25)

        assert result["ok"] is False
        assert "Rollout not found" in result["error"]

    def test_promote_rollout_invalid_target_phase(self):
        """Test rollout promotion with invalid target phase."""
        with patch("apps.hive_worker.tasks.learning.SessionLocal"):
            result = promote_rollout_task(1, "invalid_phase", 25)

            assert result["ok"] is False
            assert "Invalid target phase: invalid_phase" in result["error"]
