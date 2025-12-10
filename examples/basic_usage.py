"""
Example usage of the dqcheck library.

Run this script from the project root:
    python examples/basic_usage.py
"""

import pandas as pd

from dqcheck import DataProfiler, DataValidator, ConsoleReporter, JsonReporter


def main():
    # Create some sample data with intentional quality issues
    df = pd.DataFrame({
        "customer_id": [1, 2, 3, 4, 5, 5],  # Duplicate ID
        "name": ["Alice Smith", "Bob Jones", None, "Diana Prince", "Eve Wilson", "Frank Miller"],
        "age": [25, -5, 30, 35, 150, 42],  # Negative and unrealistic values
        "email": [
            "alice@example.com",
            "bob@test.com",
            "not-an-email",  # Invalid format
            "diana@example.com",
            "eve@example.com",
            "frank@example.com",
        ],
        "status": ["active", "inactive", "active", "pending", "unknown", "active"],
    })

    print("=" * 60)
    print("Sample Data:")
    print("=" * 60)
    print(df.to_string())
    print()

    # Profile the data
    profiler = DataProfiler(df)
    summary = profiler.summary()
    profiles = profiler.profile_all()

    reporter = ConsoleReporter()
    reporter.report_profile(profiles, summary)

    # Validate the data
    validator = DataValidator(df)
    results = (
        validator
        .column("customer_id").is_not_null().is_unique().is_positive()
        .column("name").is_not_null()
        .column("age").is_not_null().is_positive().min_value(0).max_value(120)
        .column("email").is_not_null().matches(r".+@.+\..+")
        .column("status").is_in(["active", "inactive", "pending"])
        .run()
    )

    reporter.report_validation(results)

    # Also show JSON output
    json_reporter = JsonReporter()
    print("\nJSON Output:")
    print("-" * 60)
    print(json_reporter.report_validation(results))


if __name__ == "__main__":
    main()