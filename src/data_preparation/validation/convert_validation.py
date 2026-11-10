
import json
from pathlib import Path
import pandas as pd


# 1. Define paths

PROJECT_ROOT = Path(__file__).resolve().parents[3]

VALIDATION_DIR = PROJECT_ROOT / "Data" / "Validation"
OUTPUT_DIR = PROJECT_ROOT / "CSV" / "Validation"

# Use Train CSV as the reference schema
TRAIN_CSV = PROJECT_ROOT / "CSV" / "Train" / "train.csv"

TARGET_FILES = 17

EXPECTED_TOTAL = 15290
EXPECTED_NORMAL = 6572
EXPECTED_SYBIL = 8718


# 2. Function to expand position strings

def expand_position_column(df, source_column, prefix):

    if source_column not in df.columns:
        raise ValueError(
            f"Missing column: {source_column}"
        )

    coordinates = []

    for index, value in df[source_column].items():

        if pd.isna(value):
            coordinates.append([None, None, None])
            continue

        parts = str(value).split(",")

        if len(parts) != 3:
            raise ValueError(
                f"Invalid position at row {index}: {value}"
            )

        try:
            coordinates.append(
                [float(part.strip()) for part in parts]
            )

        except ValueError:
            raise ValueError(
                f"Non-numeric position at row {index}: {value}"
            )

    coordinate_df = pd.DataFrame(
        coordinates,
        columns=[
            f"{prefix}_x",
            f"{prefix}_y",
            f"{prefix}_z"
        ],
        index=df.index
    )

    # Add the expanded numeric columns
    for column in coordinate_df.columns:
        df[column] = coordinate_df[column]

    # Remove the original string column
    df.drop(columns=[source_column], inplace=True)


# 3. Get the first 17 JSON files

json_files = sorted(
    VALIDATION_DIR.glob("*.json")
)[:TARGET_FILES]

if len(json_files) != TARGET_FILES:
    raise ValueError(
        f"Expected {TARGET_FILES} files, "
        f"but found {len(json_files)}."
    )

print("Selected JSON files:")

for file_path in json_files:
    print(file_path.name)


# 4. Read and flatten JSON messages

all_dataframes = []
total_messages = 0

for file_path in json_files:

    with open(file_path, "r", encoding="utf-8") as file:
        messages = json.load(file)

    if not isinstance(messages, list):
        raise ValueError(
            f"Unexpected JSON format: {file_path.name}"
        )

    if not all(isinstance(message, dict) for message in messages):
        raise ValueError(
            f"Some messages are not dictionaries: {file_path.name}"
        )

    # Flatten nested JSON fields
    df = pd.json_normalize(
        messages,
        sep="_"
    )

    # Expand position and position noise columns
    position_columns = {
        "receiver_pos": "receiver_pos",
        "receiver_pos_noise": "receiver_pos_noise",
        "sender_pos": "sender_pos",
        "sender_pos_noise": "sender_pos_noise"
    }

    for source_column, prefix in position_columns.items():
        expand_position_column(
            df,
            source_column,
            prefix
        )

    # Keep track of the original source
    df["source_file"] = file_path.name

    all_dataframes.append(df)

    total_messages += len(messages)

    print(
        f"{file_path.name}: "
        f"{len(messages)} messages loaded"
    )


# 5. Combine all messages

final_df = pd.concat(
    all_dataframes,
    ignore_index=True,
    sort=False
)

print("\n========== DATA SUMMARY ==========")

print(f"Selected files: {len(json_files)}")
print(f"Total messages: {total_messages}")
print(f"DataFrame rows: {len(final_df)}")
print(f"Number of columns: {len(final_df.columns)}")


# 6. Verify labels and message count

if len(final_df) != EXPECTED_TOTAL:
    raise ValueError(
        "Message count does not match the expected total!"
    )

if "attacker" not in final_df.columns:
    raise ValueError("Attacker column is missing!")

label_counts = final_df["attacker"].value_counts(
    dropna=False
)

print("\n========== LABEL DISTRIBUTION ==========")
print(label_counts)

if (
    label_counts.get(0, 0) != EXPECTED_NORMAL
    or label_counts.get(1, 0) != EXPECTED_SYBIL
):
    raise ValueError(
        "Label distribution does not match expected values!"
    )


# 7. Verify schema against Train

if not TRAIN_CSV.is_file():
    raise FileNotFoundError(
        f"Train CSV not found: {TRAIN_CSV}"
    )

train_columns = pd.read_csv(
    TRAIN_CSV,
    nrows=0
).columns.tolist()

missing_columns = set(train_columns) - set(final_df.columns)
extra_columns = set(final_df.columns) - set(train_columns)

if missing_columns or extra_columns:
    raise ValueError(
        f"Schema mismatch!\n"
        f"Missing columns: {sorted(missing_columns)}\n"
        f"Extra columns: {sorted(extra_columns)}"
    )

# Match Train column order
final_df = final_df[train_columns]

print("\nSchema matches Train successfully!")


# 8. Save CSV

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

csv_path = OUTPUT_DIR / "validation_15290_normalized.csv"

if csv_path.exists():
    raise FileExistsError(
        f"CSV already exists: {csv_path}\n"
        "Rename the existing file before running again."
    )

final_df.to_csv(
    csv_path,
    index=False,
    encoding="utf-8-sig"
)


# 9. Save selected files list

manifest_path = OUTPUT_DIR / "selected_files_normalized.txt"

with open(
    manifest_path,
    "w",
    encoding="utf-8"
) as file:

    for file_path in json_files:
        file.write(file_path.name + "\n")


# 10. Final report

print("\n====================================")
print("CSV CONVERSION COMPLETED!")
print(f"CSV file: {csv_path}")
print(f"Rows: {len(final_df)}")
print(f"Columns: {len(final_df.columns)}")
print(f"Normal: {label_counts.get(0, 0)}")
print(f"Sybil: {label_counts.get(1, 0)}")
print(f"Manifest: {manifest_path}")
print("Original JSON files were not modified.")
print("====================================")
