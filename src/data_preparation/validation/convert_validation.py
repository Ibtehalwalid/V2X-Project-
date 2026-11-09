
import json
from pathlib import Path
import pandas as pd

# 1. Define paths

PROJECT_ROOT = Path(__file__).resolve().parents[3]

VALIDATION_DIR = PROJECT_ROOT / "Data" / "Validation"
OUTPUT_DIR = PROJECT_ROOT / "CSV" / "Validation"


TARGET_FILES = 17

EXPECTED_TOTAL = 15290
EXPECTED_NORMAL = 6572
EXPECTED_SYBIL = 8718


# 2. Get the first 17 JSON files

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


# 3. Read and flatten JSON messages

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

    # Convert nested JSON fields into columns
    df = pd.json_normalize(
        messages,
        sep="_"
    )

    # Keep track of the original source
    df["source_file"] = file_path.name

    all_dataframes.append(df)

    total_messages += len(messages)

    print(
        f"{file_path.name}: "
        f"{len(messages)} messages loaded"
    )



# 4. Combine all messages

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


# 5. Verify labels and message count

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

print("\nAll validation checks passed!")

# 6. Save CSV

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

csv_path = OUTPUT_DIR / "validation_15290.csv"

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


# 7. Save selected files list

manifest_path = OUTPUT_DIR / "selected_files.txt"

with open(
    manifest_path,
    "w",
    encoding="utf-8"
) as file:

    for file_path in json_files:
        file.write(file_path.name + "\n")


# 8. Final report

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
