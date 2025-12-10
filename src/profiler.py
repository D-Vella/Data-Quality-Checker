"""
Data profiling functionality.

Generates statistical summaries and metadata about DataFrames.
"""

import pandas as pd
from typing import Any


class DataProfiler:
    """Generates statistical profiles of DataFrames."""

    def __init__(self, df: pd.DataFrame):
        """
        Initialise the profiler with a DataFrame.

        Args:
            df: The pandas DataFrame to profile.
        """
        self.df = df

    def profile_column(self, column: str) -> dict[str, Any]:
        """
        Generate a profile for a single column.

        Args:
            column: The name of the column to profile.

        Returns:
            A dictionary containing profile statistics.
        """
        series = self.df[column]
        
        profile = {
            "column": column,
            "dtype": str(series.dtype),
            "count": len(series),
            "null_count": series.isna().sum(),
            "null_percentage": round(series.isna().mean() * 100, 2),
            "unique_count": series.nunique(),
        }

        # Add numeric statistics if applicable
        if pd.api.types.is_numeric_dtype(series):
            profile.update({
                "min": series.min(),
                "max": series.max(),
                "mean": round(series.mean(), 2) if not series.isna().all() else None,
                "median": series.median() if not series.isna().all() else None,
                "std": round(series.std(), 2) if not series.isna().all() else None,
            })

        # Add string statistics if applicable
        if pd.api.types.is_string_dtype(series) or series.dtype == "object":
            non_null = series.dropna()
            if len(non_null) > 0:
                str_lengths = non_null.astype(str).str.len()
                profile.update({
                    "min_length": str_lengths.min(),
                    "max_length": str_lengths.max(),
                    "avg_length": round(str_lengths.mean(), 2),
                })

        return profile

    def profile_all(self) -> list[dict[str, Any]]:
        """
        Generate profiles for all columns in the DataFrame.

        Returns:
            A list of profile dictionaries, one per column.
        """
        return [self.profile_column(col) for col in self.df.columns]

    def summary(self) -> dict[str, Any]:
        """
        Generate a high-level summary of the DataFrame.

        Returns:
            A dictionary containing overall DataFrame statistics.
        """
        return {
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "columns": list(self.df.columns),
            "memory_usage_bytes": self.df.memory_usage(deep=True).sum(),
            "total_null_count": self.df.isna().sum().sum(),
        }