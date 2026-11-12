
from pathlib import Path
from collections import Counter
import pandas as pd

folder = Path(__file__).parent

csv_files = sorted(
    f for f in folder.glob("veh_*.csv")
    if f.name != "train.csv"
)

if not csv_files:
    raise SystemExit("ERROR: No individual vehicle CSV files found.")

frames = [pd.read_csv(f) for f in csv_files]
combined = pd.read_csv(folder / "train.csv")

# 1. Check that individual files have matching columns
columns_match = all(
    list(df.columns) == list(combined.columns)
    for df in frames
)

print("Individual CSV files:", len(csv_files))
print("Combined rows:", len(combined))
print("Combined columns:", len(combined.columns))
print("Columns match:", columns_match)

if not columns_match:
    raise SystemExit("ERROR: Column mismatch.")

# 2. Check total row count
total_rows = sum(len(df) for df in frames)
print("Sum of individual rows:", total_rows)
print("Row counts match:", total_rows == len(combined))

if total_rows != len(combined):
    raise SystemExit("ERROR: Row count mismatch.")

# 3. Check missing values and full-row duplicates
missing = int(combined.isna().sum().sum())
duplicates = int(combined.duplicated().sum())

print("Missing values:", missing)
print("Duplicate full rows:", duplicates)

# 4. Verify combined CSV contains the same rows
# as the five individual CSVs, regardless of row order.


def row_counts(df):
    normalized = df.fillna("").astype(str)
    hashes = pd.util.hash_pandas_object(
        normalized, index=False
    )
    return Counter(hashes.tolist())


individual_rows = pd.concat(frames, ignore_index=True)

same_rows = row_counts(individual_rows) == row_counts(combined)
print("Combined data matches individual files:", same_rows)

if not same_rows:
    raise SystemExit("ERROR: Combined data differs from individual files.")

print("\nCSV checks completed.")
