# test_partition_manual.py (in project root or examples/)
import pandas as pd
import numpy as np
from dqcheck import DataProfiler

# Create test data with different datetime scenarios
np.random.seed(42)

# Scenario 1: 5 years of daily data
df_daily = pd.DataFrame({
    "order_date": pd.date_range("2020-01-01", "2024-12-31", freq="D"),
    "value": np.random.randint(1, 100, size=1827)
})

# Scenario 2: Timestamps with high cardinality
df_timestamps = pd.DataFrame({
    "event_time": pd.date_range("2024-01-01", periods=10000, freq="min"),
    "value": np.random.randint(1, 100, size=10000)
})

# Scenario 3: Monthly data (low cardinality)
df_monthly = pd.DataFrame({
    "report_month": pd.date_range("2020-01-01", "2024-12-31", freq="MS"),
    "value": np.random.randint(1, 100, size=60)
})

# Run your function and see the output
result = DataProfiler(df_daily).partition_recommendations("order_date")
print(result)