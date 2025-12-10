# Data Quality Checker (dqcheck)

A lightweight Python library for validating and profiling tabular data.

## Features

- **Data Profiling**: Generate statistical summaries for your DataFrames including null counts, unique values, numeric statistics, and string length analysis
- **Flexible Validation**: Define validation rules using a fluent, chainable API
- **Multiple Output Formats**: Console output with pass/fail indicators or JSON for programmatic use

## Installation

Clone the repository and install in development mode:

```bash
git clone https://github.com/YOUR_USERNAME/Data-Quality-Checker.git
cd Data-Quality-Checker
python -m venv .venv
source .venv/Scripts/activate  # On Windows with Git Bash
pip install -e ".[dev]"
```

## Quick Start

```python
import pandas as pd
from dqcheck import DataProfiler, DataValidator, ConsoleReporter

# Load your data
df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", None],
    "age": [25, -5, 30],
})

# Profile the data
profiler = DataProfiler(df)
profiles = profiler.profile_all()
summary = profiler.summary()

reporter = ConsoleReporter()
reporter.report_profile(profiles, summary)

# Validate the data
validator = DataValidator(df)
results = (
    validator
    .column("id").is_not_null().is_unique()
    .column("name").is_not_null()
    .column("age").is_positive()
    .run()
)

reporter.report_validation(results)
```

## Available Validators

| Validator | Description |
|-----------|-------------|
| `is_not_null()` | Check that column contains no null values |
| `is_positive()` | Check that numeric values are greater than zero |
| `is_unique()` | Check that all values are unique |
| `is_in(values)` | Check that values are in an allowed list |
| `matches(pattern)` | Check that string values match a regex pattern |
| `min_value(n)` | Check that numeric values are at least n |
| `max_value(n)` | Check that numeric values are at most n |

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=dqcheck
```

## Project Structure

```
Data-Quality-Checker/
├── src/
│   └── dqcheck/
│       ├── __init__.py
│       ├── profiler.py      # Data profiling functionality
│       ├── validators.py    # Validation rules and checks
│       └── reporters.py     # Output formatting
├── tests/
│   ├── test_profiler.py
│   └── test_validators.py
├── examples/
│   └── basic_usage.py
├── pyproject.toml
└── README.md
```

## License

MIT