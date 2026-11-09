
import json
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = PROJECT_ROOT / "Data" / "Validation"

# Number of files to inspect
NUMBER_OF_FILES = 17


def count_messages(file_path):

    # Try reading a regular JSON file
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return len(data)

        elif isinstance(data, dict):

            # Check for a list of messages inside the dictionary
            for key in ["messages", "data"]:
                if key in data and isinstance(data[key], list):
                    return len(data[key])

            # A single message stored as a dictionary
            return 1

    except json.JSONDecodeError:
        # Try JSON Lines format (one JSON message per line)
        count = 0

        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    json.loads(line)
                    count += 1

        return count


def main():

    if not VALIDATION_DIR.is_dir():
        print("Validation folder not found!")
        return

    # Get JSON files and sort them by name
    json_files = sorted(
        VALIDATION_DIR.glob("*.json")
    )

    # Select first 20 files
    selected_files = json_files[:NUMBER_OF_FILES]

    if not selected_files:
        print("No JSON files found!")
        return

    total_messages = 0

    print("\n===== VALIDATION MESSAGE COUNT =====\n")

    for index, file_path in enumerate(selected_files, start=1):

        messages_count = count_messages(file_path)

        total_messages += messages_count

        print(
            f"{index}. {file_path.name} "
            f"--> {messages_count} messages"
        )

    print("\n====================================")
    print(f"Files counted: {len(selected_files)}")
    print(f"Total messages: {total_messages}")
    print("====================================")


if __name__ == "__main__":
    main()
