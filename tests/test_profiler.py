"""Tests for the profiler module."""

import pandas as pd
import pytest

from dqcheck import DataProfiler


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", None, "Eve"],
        "score": [85.5, 92.0, None, 78.5, 88.0],
    })


class TestProfileColumn:
    """Tests for column profiling."""

    def test_basic_stats(self, sample_df):
        profiler = DataProfiler(sample_df)
        profile = profiler.profile_column("id")
        
        assert profile["column"] == "id"
        assert profile["count"] == 5
        assert profile["null_count"] == 0
        assert profile["null_percentage"] == 0.0
        assert profile["unique_count"] == 5

    def test_numeric_stats(self, sample_df):
        profiler = DataProfiler(sample_df)
        profile = profiler.profile_column("id")
        
        assert profile["min"] == 1
        assert profile["max"] == 5
        assert profile["mean"] == 3.0
        assert profile["median"] == 3.0

    def test_string_stats(self, sample_df):
        profiler = DataProfiler(sample_df)
        profile = profiler.profile_column("name")
        
        assert "min_length" in profile
        assert "max_length" in profile
        assert "avg_length" in profile

    def test_handles_nulls(self, sample_df):
        profiler = DataProfiler(sample_df)
        profile = profiler.profile_column("name")
        
        assert profile["null_count"] == 1
        assert profile["null_percentage"] == 20.0

    def test_partition_recommendations(self, sample_df):
        profiler = DataProfiler(sample_df)
        
        # Capture the printed output
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        profiler.partition_recommendations("name")
        
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "Observations:" in output
        assert "Unique entries in 'category' column" in output
        assert "Total entries in DataFrame" in output
        assert "is of type" in output
        assert "Score" in output


class TestProfileAll:
    """Tests for profiling all columns."""

    def test_returns_all_columns(self, sample_df):
        profiler = DataProfiler(sample_df)
        profiles = profiler.profile_all()
        
        assert len(profiles) == 3
        columns = [p["column"] for p in profiles]
        assert "id" in columns
        assert "name" in columns
        assert "score" in columns


class TestSummary:
    """Tests for DataFrame summary."""

    def test_summary_stats(self, sample_df):
        profiler = DataProfiler(sample_df)
        summary = profiler.summary()
        
        assert summary["row_count"] == 5
        assert summary["column_count"] == 3
        assert set(summary["columns"]) == {"id", "name", "score"}
        assert summary["total_null_count"] == 2  # 1 in name, 1 in score
        assert summary["memory_usage_bytes"] > 0