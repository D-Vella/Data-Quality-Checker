"""
Data validation functionality.

Provides rule-based validation checks for DataFrames.
"""

import pandas as pd
from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Represents the result of a single validation check."""
    
    check_name: str
    passed: bool
    column: str | None = None
    message: str = ""
    failing_count: int = 0
    failing_examples: list[Any] = field(default_factory=list)


class DataValidator:
    """
    Validates DataFrames against a set of rules.
    
    Provides a fluent interface for building validation checks.
    
    Example:
        validator = DataValidator(df)
        results = (
            validator
            .column("age").is_not_null().is_positive()
            .column("email").matches(r".+@.+\..+")
            .run()
        )
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialise the validator with a DataFrame.

        Args:
            df: The pandas DataFrame to validate.
        """
        self.df = df
        self._checks: list[tuple[str, str | None, Callable[[], ValidationResult]]] = []
        self._current_column: str | None = None

    def column(self, name: str) -> "DataValidator":
        """
        Set the current column for subsequent checks.

        Args:
            name: The name of the column to validate.

        Returns:
            Self for method chaining.
        """
        if name not in self.df.columns:
            raise ValueError(f"Column '{name}' not found in DataFrame")
        self._current_column = name
        return self

    def _add_check(
        self, 
        check_name: str, 
        check_fn: Callable[[], ValidationResult]
    ) -> "DataValidator":
        """Add a check to the validation queue."""
        self._checks.append((check_name, self._current_column, check_fn))
        return self

    def is_not_null(self) -> "DataValidator":
        """Check that the current column contains no null values."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col]
            null_mask = series.isna()
            failing = null_mask.sum()
            
            return ValidationResult(
                check_name="is_not_null",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} null values" if failing > 0 else "No null values",
                failing_count=failing,
                failing_examples=self.df[null_mask].index.tolist()[:5],
            )
        
        return self._add_check("is_not_null", check)

    def is_positive(self) -> "DataValidator":
        """Check that numeric values in the current column are positive (> 0)."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col]
            if not pd.api.types.is_numeric_dtype(series):
                return ValidationResult(
                    check_name="is_positive",
                    column=col,
                    passed=False,
                    message=f"Column '{col}' is not numeric",
                )
            
            non_positive_mask = series.fillna(1) <= 0  # Ignore nulls for this check
            failing = non_positive_mask.sum()
            
            return ValidationResult(
                check_name="is_positive",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} non-positive values" if failing > 0 else "All values positive",
                failing_count=failing,
                failing_examples=self.df[non_positive_mask][col].tolist()[:5],
            )
        
        return self._add_check("is_positive", check)

    def is_in(self, allowed_values: list[Any]) -> "DataValidator":
        """Check that all values in the current column are in the allowed list."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col]
            invalid_mask = ~series.isin(allowed_values) & series.notna()
            failing = invalid_mask.sum()
            
            return ValidationResult(
                check_name="is_in",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} values not in allowed list" if failing > 0 else "All values valid",
                failing_count=failing,
                failing_examples=self.df[invalid_mask][col].unique().tolist()[:5],
            )
        
        return self._add_check("is_in", check)

    def matches(self, pattern: str) -> "DataValidator":
        """Check that string values in the current column match a regex pattern."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col].astype(str)
            match_mask = series.str.match(pattern, na=False)
            non_match_mask = ~match_mask & self.df[col].notna()
            failing = non_match_mask.sum()
            
            return ValidationResult(
                check_name="matches",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} values not matching pattern" if failing > 0 else "All values match pattern",
                failing_count=failing,
                failing_examples=self.df[non_match_mask][col].tolist()[:5],
            )
        
        return self._add_check("matches", check)

    def min_value(self, minimum: float) -> "DataValidator":
        """Check that numeric values are at least the specified minimum."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col]
            if not pd.api.types.is_numeric_dtype(series):
                return ValidationResult(
                    check_name="min_value",
                    column=col,
                    passed=False,
                    message=f"Column '{col}' is not numeric",
                )
            
            below_min_mask = series < minimum
            failing = below_min_mask.sum()
            
            return ValidationResult(
                check_name="min_value",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} values below {minimum}" if failing > 0 else f"All values >= {minimum}",
                failing_count=failing,
                failing_examples=self.df[below_min_mask][col].tolist()[:5],
            )
        
        return self._add_check("min_value", check)

    def max_value(self, maximum: float) -> "DataValidator":
        """Check that numeric values are at most the specified maximum."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col]
            if not pd.api.types.is_numeric_dtype(series):
                return ValidationResult(
                    check_name="max_value",
                    column=col,
                    passed=False,
                    message=f"Column '{col}' is not numeric",
                )
            
            above_max_mask = series > maximum
            failing = above_max_mask.sum()
            
            return ValidationResult(
                check_name="max_value",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} values above {maximum}" if failing > 0 else f"All values <= {maximum}",
                failing_count=failing,
                failing_examples=self.df[above_max_mask][col].tolist()[:5],
            )
        
        return self._add_check("max_value", check)

    def is_unique(self) -> "DataValidator":
        """Check that all values in the current column are unique."""
        col = self._current_column
        
        def check() -> ValidationResult:
            series = self.df[col]
            duplicate_mask = series.duplicated(keep=False)
            failing = duplicate_mask.sum()
            
            return ValidationResult(
                check_name="is_unique",
                column=col,
                passed=failing == 0,
                message=f"Found {failing} duplicate values" if failing > 0 else "All values unique",
                failing_count=failing,
                failing_examples=series[series.duplicated(keep='first')].tolist()[:5],
            )
        
        return self._add_check("is_unique", check)

    def run(self) -> list[ValidationResult]:
        """
        Execute all queued validation checks.

        Returns:
            A list of ValidationResult objects.
        """
        return [check_fn() for _, _, check_fn in self._checks]