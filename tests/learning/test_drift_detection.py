"""Unit tests for learning drift detection functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from apps.hive_worker.tasks.learning import detect_drift


class TestDriftDetection:
    """Test suite for feature drift detection."""

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_drift_detection_no_drift(self, mock_session_local):
        """Test drift detection when no significant drift is detected."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        # Mock feature snapshots query
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch("random.uniform", return_value=0.2):  # Low drift score
            result = detect_drift("pricing", 1)

        assert result["ok"] is True
        assert result["drift_detected"] is False
        assert result["drift_score"] == 0.2
        mock_db.close.assert_called_once()

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_drift_detection_high_drift(self, mock_session_local):
        """Test drift detection when high drift is detected."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        # Mock feature snapshots
        mock_features = [Mock() for _ in range(50)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_features

        # Mock drift report creation
        mock_drift_report = Mock()
        mock_drift_report.id = 123

        with patch("random.uniform", return_value=0.9):  # High drift score
            result = detect_drift("pricing", 1)

        assert result["ok"] is True
        assert result["drift_detected"] is True
        assert result["drift_score"] == 0.9
        assert result["severity"] == "critical"
        assert result["report_id"] == 123

        # Verify drift report was added and committed
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_drift_detection_database_error(self, mock_session_local):
        """Test drift detection handles database errors gracefully."""
        mock_session_local.side_effect = Exception("Database connection failed")

        result = detect_drift("pricing", 1)

        assert result["ok"] is False
        assert "error" in result
        assert "Database connection failed" in result["error"]

    def test_drift_severity_classification(self):
        """Test drift severity is classified correctly based on score."""
        test_cases = [
            (0.1, "low"),
            (0.3, "low"),
            (0.5, "medium"),
            (0.7, "high"),
            (0.9, "critical"),
        ]

        for score, expected_severity in test_cases:
            with patch("apps.hive_worker.tasks.learning.SessionLocal"):
                with patch("random.uniform", return_value=score):
                    result = detect_drift("test_brain", 1)

                    if score > 0.3:  # Drift detected
                        assert result["severity"] == expected_severity
