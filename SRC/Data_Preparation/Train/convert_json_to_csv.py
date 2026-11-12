
import json
import csv
from pathlib import Path

# Input and output folders
input_dir = Path("../../Data/Train")
output_dir = Path(".")
output_dir.mkdir(parents=True, exist_ok=True)


def flatten_message(message):
    """Convert nested message fields into flat CSV columns."""
    row = {}

    for key, value in message.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                column = f"{key}_{subkey}"

                # Split 3D position/noise vectors into separate columns
                if (
                    subkey in ("pos", "pos_noise")
                    and isinstance(subvalue, str)
                ):
                    parts = subvalue.split(",")
                    if len(parts) == 3:
                        for axis, part in zip(("x", "y", "z"), parts):
                            try:
                                row[f"{column}_{axis}"] = float(part.strip())
                            except ValueError:
                                row[f"{column}_{axis}"] = part.strip()
                        continue

                row[column] = subvalue

        elif isinstance(value, (list, dict)):
            row[key] = json.dumps(value, ensure_ascii=False)

        else:
            row[key] = value

    return row


all_rows = []
files = sorted(input_dir.glob("*.json"))

if not files:
    raise SystemExit(f"No JSON files found in {input_dir.resolve()}")

for file_path in files:
    print(f"Reading: {file_path.name}")

    with file_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        raise ValueError(f"Unexpected JSON structure in {file_path.name}")

    rows = []

    for message in data:
        if not isinstance(message, dict):
            continue

        row = flatten_message(message)
        row["source_file"] = file_path.name
        rows.append(row)

    if not rows:
        print(f"Warning: no message records in {file_path.name}")
        continue

    # Save an individual CSV for each JSON file
    columns = list(dict.fromkeys(
        key for row in rows for key in row.keys()
    ))

    output_file = output_dir / f"{file_path.stem}.csv"

    with output_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    all_rows.extend(rows)
    print(f"Saved: {output_file} ({len(rows)} messages)")

# Save all five files together for model training
if all_rows:
    columns = list(dict.fromkeys(
        key for row in all_rows for key in row.keys()
    ))

    combined_file = output_dir / "train.csv"

    with combined_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_rows)

    print("\nConversion completed successfully!")
    print(f"JSON files processed: {len(files)}")
    print(f"Total messages: {len(all_rows)}")
    print(f"Combined CSV: {combined_file.resolve()}")
else:
    print("No records were converted.")
