
from pathlib import Path
import pandas as pd

# ==========================================
# 1. Project paths
# ==========================================

PROJECT_ROOT = Path(r"C:\CS\V2X-Project-")

SPLIT_DIRS = {
    "Train": PROJECT_ROOT / "CSV" / "Train" / "train.csv",
    "Validation": PROJECT_ROOT / "CSV" / "Validation" / "validation_15290.csv",
    "Test": PROJECT_ROOT / "CSV" / "Test" / "Test_15,500 Messages.csv",
}

# ==========================================
# 2. Load the specified CSV files
# ==========================================

datasets = {}

for split_name, file_path in SPLIT_DIRS.items():

    if not file_path.is_file():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    datasets[split_name] = df

    print(f"\n{split_name}")
    print(f"File: {file_path.name}")
    print(f"Messages: {len(df):,}")

# ==========================================
# 3. Check columns
# ==========================================

print("\n========== COLUMNS ==========")

for name, df in datasets.items():
    print(f"\n{name}:")
    print(df.columns.tolist())

# ==========================================
# 4. Check label distribution
# ==========================================

print("\n========== LABEL DISTRIBUTION ==========")

label_candidates = [
    "label",
    "attacker",
    "class",
    "target"
]

label_col = next(
    (
        col for col in datasets["Train"].columns
        if col.lower() in label_candidates
    ),
    None
)

if label_col is None:
    print("No label column detected.")
    print("Check the printed column names.")
else:
    for name, df in datasets.items():

        if label_col not in df.columns:
            print(f"{name}: label column missing")
            continue

        print(f"\n{name}:")

        print(
            df[label_col]
            .value_counts(dropna=False)
        )

        print(
            (df[label_col].value_counts(normalize=True) * 100)
            .round(2)
            .astype(str) + "%"
        )

# ==========================================
# 5. Compare numerical feature distributions
# ==========================================

print("\n========== NUMERICAL FEATURE DISTRIBUTION ==========")

common_columns = set(datasets["Train"].columns)

for df in datasets.values():
    common_columns.intersection_update(df.columns)

excluded_columns = {
    "label", "attacker", "class", "target",
    "sender_id", "sender_alias", "sender",
    "receiver", "messageid", "message_id",
    "sendtime", "rcvtime", "receive_time"
}

numeric_features = []

for col in common_columns:

    if col.lower() in excluded_columns:
        continue

    if all(
        pd.api.types.is_numeric_dtype(df[col])
        for df in datasets.values()
    ):
        numeric_features.append(col)

for feature in sorted(numeric_features):

    print(f"\nFeature: {feature}")

    for name, df in datasets.items():

        stats = df[feature].describe(
            percentiles=[0.25, 0.50, 0.75]
        )

        print(
            f"{name}: "
            f"mean={stats['mean']:.4f}, "
            f"std={stats['std']:.4f}, "
            f"median={stats['50%']:.4f}, "
            f"Q1={stats['25%']:.4f}, "
            f"Q3={stats['75%']:.4f}"
        )

# ==========================================
# 6. Check exact duplicate rows across splits
# ==========================================

print("\n========== EXACT DUPLICATE ROWS ==========")

split_hashes = {}

for name, df in datasets.items():

    # Use columns shared by all splits
    common_df = df[sorted(common_columns)].copy()

    split_hashes[name] = set(
        pd.util.hash_pandas_object(
            common_df,
            index=False
        )
    )

split_names = list(split_hashes.keys())

for i in range(len(split_names)):
    for j in range(i + 1, len(split_names)):

        first = split_names[i]
        second = split_names[j]

        overlap = (
            split_hashes[first]
            & split_hashes[second]
        )

        print(
            f"{first} vs {second}: "
            f"{len(overlap):,} matching row hashes"
        )

# ==========================================
# 7. Check message identity overlap
# ==========================================

print("\n========== MESSAGE IDENTITY OVERLAP ==========")

column_lookup = {
    col.lower(): col
    for col in datasets["Train"].columns
}

possible_keys = [
    "sender_id",
    "messageid",
    "sendtime",
    "receiver"
]

key_columns = [
    column_lookup[col]
    for col in possible_keys
    if col in column_lookup
]

if (
    "sender_id" in column_lookup
    and "messageid" in column_lookup
    and "sendtime" in column_lookup
):

    print("Identity columns:", key_columns)

    identity_sets = {}

    for name, df in datasets.items():

        available_keys = [
            col for col in key_columns
            if col in df.columns
        ]

        identity_sets[name] = set(
            map(
                tuple,
                df[available_keys]
                .dropna()
                .astype(str)
                .values
            )
        )

    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):

            first = split_names[i]
            second = split_names[j]

            overlap = (
                identity_sets[first]
                & identity_sets[second]
            )

            print(
                f"{first} vs {second}: "
                f"{len(overlap):,} matching identities"
            )

else:
    print(
        "Could not check message identity: "
        "sender_id, messageID and sendTime are required."
    )

print("\n========== CHECK COMPLETED ==========")
