"""
Data profiling functionality.

Generates statistical summaries and metadata about DataFrames.
"""

import pandas as pd
from  pandas.api import types as ptypes
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

    
    @staticmethod
    def is_categorical_dtype(series_or_dtype) -> bool:
        """
        Replacement for deprecated ptypes.is_categorical_dtype

        Accepts either a pd.Series or a dtype-like object.
        """
        dtype = getattr(series_or_dtype, "dtype", series_or_dtype)
        # dtype.name == "category" handles string descriptions like 'category'
        return getattr(dtype, "name", None) == "category" or isinstance(dtype, pd.CategoricalDtype)

    def is_partitionable_dtype(self, series: pd.Series) -> bool:
        """
        Return True if we can reasonably provide partitioning recommendations.
        Args:
            series: The pandas Series to check.

        Returns:
            bool: True if the series is of a partitionable dtype.
        """
        return (
            ptypes.is_string_dtype(series)
            or self.is_categorical_dtype(series)
            or ptypes.is_datetime64_any_dtype(series)
            or ptypes.is_integer_dtype(series)
            or ptypes.is_float_dtype(series)
            or ptypes.is_bool_dtype(series)
        )

    def recommend_datetime_grouping(self, series: pd.Series) -> dict[str, Any]:
        """
        Recommend the best datetime partitioning granularity based on data analysis.

        Args:
            series: A datetime pandas Series.

        Returns:
            A dictionary with grouping recommendation, cardinality info, and score.
        """
        clean_series = series.dropna()
        if len(clean_series) == 0:
            return {
                "recommended_grouping": None,
                "cardinalities": {},
                "reason": "No non-null datetime values",
                "score": -1
            }

        # Calculate cardinality at different time periods
        dt_checks = {
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'M',
            'quarterly': 'Q',
            'yearly': 'Y'
        }

        cardinalities = {}
        for check_name, freq in dt_checks.items():
            try:
                # to_period handles non-fixed frequencies safely (e.g., 'M', 'Q', 'Y')
                cardinalities[check_name] = clean_series.dt.to_period(freq).nunique()
            except Exception:
                # Fallback for fixed-length frequencies (days, weeks)
                cardinalities[check_name] = clean_series.dt.floor(freq).nunique()

        # Find the optimal grouping level (aim for 10-1000 partitions)
        # Priority: medium cardinality (10-1000) > lower cardinality
        optimal_range = (10, 1000)
        good_range = (100, 1000)
        excellent_range = (10, 100)

        best_grouping = None
        best_score = -1
        reason = ""

        # Check in order of typical preference (most granular first for tie-breaking)
        for grouping in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']:
            card = cardinalities[grouping]

            if excellent_range[0] <= card <= excellent_range[1]:
                # Excellent range: prefer this
                if best_grouping is None or best_score < 2:
                    best_grouping = grouping
                    best_score = 2
                    reason = f"{grouping.capitalize()} partitioning provides excellent partition count ({card})"
            elif good_range[0] < card <= good_range[1]:
                # Good range: acceptable
                if best_grouping is None or best_score < 1:
                    best_grouping = grouping
                    best_score = 1
                    reason = f"{grouping.capitalize()} partitioning provides good partition count ({card})"
            elif optimal_range[0] <= card < good_range[0]:
                # Low-medium range: usable
                if best_grouping is None or best_score < 1:
                    best_grouping = grouping
                    best_score = 1
                    reason = f"{grouping.capitalize()} partitioning provides adequate partition count ({card})"

        # If no good option found, pick the one closest to optimal range
        if best_grouping is None:
            # Find the grouping with cardinality closest to 100 (middle of excellent range)
            target = 100
            best_grouping = min(cardinalities.keys(),
                              key=lambda k: abs(cardinalities[k] - target))
            card = cardinalities[best_grouping]

            if card < optimal_range[0]:
                best_score = 0
                reason = f"{best_grouping.capitalize()} partitioning has low partition count ({card}), but is the best available option"
            else:  # card > optimal_range[1]
                best_score = -1
                reason = f"{best_grouping.capitalize()} partitioning has high partition count ({card}), may lead to too many partitions"

        return {
            "recommended_grouping": best_grouping,
            "cardinalities": cardinalities,
            "partition_count": cardinalities[best_grouping],
            "reason": reason,
            "score": best_score
        }

    def partition_recommendations(self, column: str):
        """
        Function to give partitioning recommendations based on column skewness and cardinality.
        
        Args:
            column: The name of the column to analyze.
        
        Returns:
            Prints observations and a recommended score for partitioning.
        """
        #profile the column
        profile_results = self.profile_column(column)

        if not self.is_partitionable_dtype(self.df[column]):
            print(f"Column '{column}' is of type '{profile_results['dtype']}'. Not recommended for partitioning.")
            return

        print(f"Column '{column}' is of type '{profile_results['dtype']}'.")

        # Check if this is a datetime column
        is_datetime = ptypes.is_datetime64_any_dtype(self.df[column])

        print("="*40)
        print("Observations:")

        if profile_results["null_count"] > 0:
            print(f"WARNING: Null values in '{column}' column: {profile_results['null_count']} ({profile_results['null_percentage']}%)")
            print("Consider handling nulls before partitioning, depending on implementation NULL values can cause data skew over time.")

        if is_datetime:
            # DateTime-specific analysis
            datetime_analysis = self.recommend_datetime_grouping(self.df[column])

            if datetime_analysis["recommended_grouping"] is None:
                print("No valid datetime values found for partitioning analysis.")
                return

            # Show cardinality at all time periods
            print("\nCardinality at different time periods:")
            for period, count in datetime_analysis["cardinalities"].items():
                marker = " ← RECOMMENDED" if period == datetime_analysis["recommended_grouping"] else ""
                print(f"  {period.capitalize()}: {count}{marker}")

            print(f"\nRecommended grouping: {datetime_analysis['recommended_grouping'].upper()}")
            print(f"Reason: {datetime_analysis['reason']}")

            print("="*40)
            print("Recommendation:")
            recommendation_score = datetime_analysis['score']

            if datetime_analysis['score'] == 2:
                print(f"Excellent partitioning strategy. Score +2")
            elif datetime_analysis['score'] == 1:
                print(f"Good partitioning strategy. Score +1")
            elif datetime_analysis['score'] == 0:
                print(f"Acceptable partitioning strategy. Score +0")
            else:
                print(f"Suboptimal partitioning count. Score -1")

            print(f"\nColumn '{column}' recommended score: {recommendation_score} / 2. Higher is better.")
            print(f"Suggested partition strategy: Partition by {datetime_analysis['recommended_grouping']}")
            print("="*40)

        else:
            # Non-datetime analysis (existing logic)
            Cardinality = profile_results["unique_count"]
            print(f"Unique entries in '{column}' column: {Cardinality}")

            total_entries = profile_results["count"]
            print(f"Total entries in DataFrame: {total_entries}")

            # Check the distribution
            distribution_df = self.df[column].value_counts(normalize=True)

            biggest_entry = distribution_df.max()  # Proportion of the most frequent category
            print(f"Biggest entry proportion in '{column}' column: {biggest_entry:.2%}")

            skew_factor = biggest_entry / distribution_df.mean()
            print(f"Skew factor of '{column}' column: {skew_factor:.2f}. 1.0 means no skew. 2.0 means the biggest entry is twice the average.")

            print("="*40)
            print("Recommendation:")
            recommendation_score = 0

            if skew_factor > 5.0:
                recommendation_score += -1
                print(f"The '{column}' column is highly skewed. Score -1")
            elif skew_factor > 2.0:
                recommendation_score += 0
                print(f"The '{column}' column is moderately skewed. Score +0")
            else:
                recommendation_score += 1
                print(f"The '{column}' column has low skew. Score +1")

            if Cardinality < 100:
                recommendation_score += 0
                print("This column has low cardinality. Score +0")
            elif Cardinality < 1000:
                recommendation_score += 1 #Maybe a hot take but I would having a medium cardinality means you get better performance from partitioning.
                print("This column has medium cardinality. Score +1")
            else:
                recommendation_score += -1
                print("This column has high cardinality. Score -1")

            print(f"\nColumn '{column}' recommended score: {recommendation_score} / 2. Higher is better.")
            print("="*40)