"""Unit tests for learning benchmark execution functionality."""

import pytest
from unittest.mock import Mock, patch
import json

from apps.hive_worker.tasks.learning import run_benchmark


class TestBenchmarkRunner:
    """Test suite for benchmark execution."""

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_benchmark_execution_success(self, mock_session_local):
        """Test successful benchmark execution and persistence."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_benchmark = Mock()
        mock_benchmark.id = 456

        with patch("random.uniform", side_effect=[0.85, 0.8, 0.75, 0.82]):
            with patch("random.randint", return_value=5000):
                result = run_benchmark(1, "accuracy_test", "validation_set_v1")

        assert result["ok"] is True
        assert result["benchmark_id"] == 456
        assert 0.5 <= result["score"] <= 0.95
        assert "report" in result
        assert result["report"]["benchmark_name"] == "accuracy_test"
        assert result["report"]["dataset_ref"] == "validation_set_v1"

        # Verify benchmark was added and committed
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @patch("apps.hive_worker.tasks.learning.SessionLocal")
    def test_benchmark_database_error(self, mock_session_local):
        """Test benchmark handles database errors gracefully."""
        mock_session_local.side_effect = Exception("Database error")

        result = run_benchmark(1, "test_benchmark")

        assert result["ok"] is False
        assert "error" in result
        assert "Database error" in result["error"]

    def test_benchmark_report_structure(self):
        """Test benchmark report contains all required metrics."""
        with patch("apps.hive_worker.tasks.learning.SessionLocal"):
            with patch("random.uniform", side_effect=[0.85, 0.8, 0.75, 0.82]):
                with patch("random.randint", return_value=5000):
                    result = run_benchmark(1, "comprehensive_test", "test_dataset")

        report = result["report"]
        required_fields = [
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "samples_evaluated",
            "benchmark_name",
            "dataset_ref",
        ]

        for field in required_fields:
            assert field in report, f"Missing required field: {field}"

        # Verify numeric fields are within expected ranges
        assert 0.0 <= report["accuracy"] <= 1.0
        assert 0.0 <= report["precision"] <= 1.0
        assert 0.0 <= report["recall"] <= 1.0
        assert 0.0 <= report["f1_score"] <= 1.0
        assert report["samples_evaluated"] > 0
