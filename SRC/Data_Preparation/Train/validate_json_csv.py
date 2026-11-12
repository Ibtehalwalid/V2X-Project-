
import csv
import json
import io
from pathlib import Path

base = Path(__file__).parent
input_dir = base / "../../Data/Train"


def flatten_message(message):
    row = {}

    for key, value in message.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                column = f"{key}_{subkey}"

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

        elif isinstance(value, list):
            row[key] = json.dumps(value, ensure_ascii=False)
        else:
            row[key] = value

    return row


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def expected_csv(rows):
    columns = list(dict.fromkeys(
        key for row in rows for key in row.keys()
    ))

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

    buffer.seek(0)
    reader = csv.DictReader(buffer)
    return reader.fieldnames, list(reader)


json_files = sorted(input_dir.glob("*.json"))

if not json_files:
    raise SystemExit(f"FAIL: No JSON files found in {input_dir.resolve()}")

all_rows = []
errors = []

for json_path in json_files:
    with json_path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        errors.append(f"{json_path.name}: unexpected JSON structure")
        continue

    rows = []

    for message in data:
        if not isinstance(message, dict):
            continue

        row = flatten_message(message)
        row["source_file"] = json_path.name
        rows.append(row)

    csv_path = base / f"{json_path.stem}.csv"

    if not csv_path.exists():
        errors.append(f"{json_path.name}: missing CSV {csv_path.name}")
        continue

    actual_header, actual_rows = read_csv(csv_path)
    expected_header, expected_rows = expected_csv(rows)

    if actual_header != expected_header:
        errors.append(f"{csv_path.name}: column names/order differ")
    elif actual_rows != expected_rows:
        errors.append(
            f"{csv_path.name}: cell values differ from JSON conversion")
    else:
        print(f"PASS: {json_path.name} -> {csv_path.name} ({len(rows)} rows)")

    all_rows.extend(rows)

combined_path = base / "train.csv"

if not combined_path.exists():
    errors.append("Missing combined train.csv")
else:
    actual_header, actual_rows = read_csv(combined_path)
    expected_header, expected_rows = expected_csv(all_rows)

    if actual_header != expected_header:
        errors.append("train.csv: column names/order differ")
    elif actual_rows != expected_rows:
        errors.append("train.csv: cell values differ from JSON conversion")
    else:
        print(f"PASS: train.csv ({len(all_rows)} rows)")

if errors:
    print("\nVALIDATION FAILED:")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print("\nSUCCESS: CSV files match the JSON-to-CSV conversion.")
print(f"JSON files checked: {len(json_files)}")
print(f"Total messages checked: {len(all_rows)}")
