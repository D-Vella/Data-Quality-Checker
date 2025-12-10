"""
Reporting functionality.

Formats and outputs validation results and profiles.
"""

import json
from typing import Any

from .validators import ValidationResult


class ConsoleReporter:
    """Outputs validation results to the console."""

    def report_validation(self, results: list[ValidationResult]) -> None:
        """
        Print validation results to the console.

        Args:
            results: List of ValidationResult objects to report.
        """
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        for result in results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            col_info = f"[{result.column}]" if result.column else ""
            print(f"\n{status} {col_info} {result.check_name}")
            print(f"       {result.message}")
            
            if not result.passed and result.failing_examples:
                examples = ", ".join(str(x) for x in result.failing_examples[:3])
                print(f"       Examples: {examples}")

        print("\n" + "-" * 60)
        print(f"SUMMARY: {passed} passed, {failed} failed, {len(results)} total")
        print("=" * 60 + "\n")

    def report_profile(self, profiles: list[dict[str, Any]], summary: dict[str, Any] | None = None) -> None:
        """
        Print profile results to the console.

        Args:
            profiles: List of column profile dictionaries.
            summary: Optional overall DataFrame summary.
        """
        print("\n" + "=" * 60)
        print("DATA PROFILE")
        print("=" * 60)

        if summary:
            print(f"\nDataFrame: {summary['row_count']} rows × {summary['column_count']} columns")
            print(f"Memory usage: {summary['memory_usage_bytes'] / 1024:.2f} KB")
            print(f"Total nulls: {summary['total_null_count']}")

        for profile in profiles:
            print(f"\n--- {profile['column']} ({profile['dtype']}) ---")
            print(f"    Non-null: {profile['count'] - profile['null_count']} / {profile['count']}")
            print(f"    Null %: {profile['null_percentage']}%")
            print(f"    Unique: {profile['unique_count']}")
            
            if "min" in profile:
                print(f"    Min: {profile['min']}, Max: {profile['max']}")
                print(f"    Mean: {profile['mean']}, Median: {profile['median']}")
            
            if "min_length" in profile:
                print(f"    Length: {profile['min_length']} - {profile['max_length']} (avg: {profile['avg_length']})")

        print("\n" + "=" * 60 + "\n")


class JsonReporter:
    """Outputs validation results and profiles as JSON."""

    def validation_to_dict(self, results: list[ValidationResult]) -> dict[str, Any]:
        """
        Convert validation results to a dictionary.

        Args:
            results: List of ValidationResult objects.

        Returns:
            A dictionary representation of the results.
        """
        passed = sum(1 for r in results if r.passed)
        
        return {
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": len(results) - passed,
                "success": passed == len(results),
            },
            "results": [
                {
                    "check_name": r.check_name,
                    "column": r.column,
                    "passed": r.passed,
                    "message": r.message,
                    "failing_count": r.failing_count,
                    "failing_examples": r.failing_examples,
                }
                for r in results
            ],
        }

    def report_validation(self, results: list[ValidationResult], indent: int = 2) -> str:
        """
        Convert validation results to a JSON string.

        Args:
            results: List of ValidationResult objects.
            indent: JSON indentation level.

        Returns:
            A JSON string representation of the results.
        """
        return json.dumps(self.validation_to_dict(results), indent=indent, default=str)

    def report_profile(
        self, 
        profiles: list[dict[str, Any]], 
        summary: dict[str, Any] | None = None,
        indent: int = 2
    ) -> str:
        """
        Convert profile results to a JSON string.

        Args:
            profiles: List of column profile dictionaries.
            summary: Optional overall DataFrame summary.
            indent: JSON indentation level.

        Returns:
            A JSON string representation of the profile.
        """
        output = {
            "summary": summary,
            "columns": profiles,
        }
        return json.dumps(output, indent=indent, default=str)