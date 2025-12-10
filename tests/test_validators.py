"""Tests for the validators module."""

import pandas as pd
import pytest

from dqcheck import DataValidator


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", None, "Eve"],
        "age": [25, -5, 30, 35, 150],
        "email": ["alice@example.com", "bob@test.com", "invalid", "diana@example.com", "eve@example.com"],
        "status": ["active", "inactive", "active", "pending", "unknown"],
    })


class TestIsNotNull:
    """Tests for the is_not_null validator."""

    def test_passes_when_no_nulls(self, sample_df):
        result = DataValidator(sample_df).column("id").is_not_null().run()[0]
        assert result.passed is True
        assert result.failing_count == 0

    def test_fails_when_nulls_present(self, sample_df):
        result = DataValidator(sample_df).column("name").is_not_null().run()[0]
        assert result.passed is False
        assert result.failing_count == 1


class TestIsPositive:
    """Tests for the is_positive validator."""

    def test_passes_when_all_positive(self, sample_df):
        result = DataValidator(sample_df).column("id").is_positive().run()[0]
        assert result.passed is True

    def test_fails_when_negative_present(self, sample_df):
        result = DataValidator(sample_df).column("age").is_positive().run()[0]
        assert result.passed is False
        assert -5 in result.failing_examples


class TestIsIn:
    """Tests for the is_in validator."""

    def test_passes_when_all_valid(self, sample_df):
        allowed = ["active", "inactive", "pending", "unknown"]
        result = DataValidator(sample_df).column("status").is_in(allowed).run()[0]
        assert result.passed is True

    def test_fails_when_invalid_present(self, sample_df):
        allowed = ["active", "inactive"]
        result = DataValidator(sample_df).column("status").is_in(allowed).run()[0]
        assert result.passed is False


class TestMatches:
    """Tests for the matches validator."""

    def test_passes_when_all_match(self):
        df = pd.DataFrame({"code": ["ABC123", "DEF456", "GHI789"]})
        result = DataValidator(df).column("code").matches(r"^[A-Z]{3}\d{3}$").run()[0]
        assert result.passed is True

    def test_fails_when_no_match(self, sample_df):
        result = DataValidator(sample_df).column("email").matches(r".+@.+\..+").run()[0]
        assert result.passed is False
        assert "invalid" in result.failing_examples


class TestMinMaxValue:
    """Tests for min_value and max_value validators."""

    def test_min_value_passes(self, sample_df):
        result = DataValidator(sample_df).column("age").min_value(-10).run()[0]
        assert result.passed is True

    def test_min_value_fails(self, sample_df):
        result = DataValidator(sample_df).column("age").min_value(0).run()[0]
        assert result.passed is False

    def test_max_value_passes(self, sample_df):
        result = DataValidator(sample_df).column("age").max_value(200).run()[0]
        assert result.passed is True

    def test_max_value_fails(self, sample_df):
        result = DataValidator(sample_df).column("age").max_value(100).run()[0]
        assert result.passed is False


class TestIsUnique:
    """Tests for the is_unique validator."""

    def test_passes_when_unique(self, sample_df):
        result = DataValidator(sample_df).column("id").is_unique().run()[0]
        assert result.passed is True

    def test_fails_when_duplicates(self):
        df = pd.DataFrame({"value": [1, 2, 2, 3]})
        result = DataValidator(df).column("value").is_unique().run()[0]
        assert result.passed is False


class TestChaining:
    """Tests for chaining multiple validators."""

    def test_multiple_checks_on_same_column(self, sample_df):
        results = (
            DataValidator(sample_df)
            .column("age")
            .is_not_null()
            .is_positive()
            .max_value(120)
            .run()
        )
        assert len(results) == 3
        assert results[0].passed is True  # is_not_null
        assert results[1].passed is False  # is_positive (has -5)
        assert results[2].passed is False  # max_value (has 150)

    def test_multiple_columns(self, sample_df):
        results = (
            DataValidator(sample_df)
            .column("id").is_not_null().is_positive()
            .column("name").is_not_null()
            .run()
        )
        assert len(results) == 3
        assert results[0].column == "id"
        assert results[1].column == "id"
        assert results[2].column == "name"