
import json
from pathlib import Path
from collections import Counter

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = PROJECT_ROOT / "Data" / "Validation"

files = sorted(VALIDATION_DIR.glob("*.json"))[:20]

total = Counter()

print("\n===== ATTACKER DISTRIBUTION =====\n")

for file_path in files:

    with open(file_path, "r", encoding="utf-8") as file:
        messages = json.load(file)

    labels = Counter(
        message.get("attacker")
        for message in messages
    )

    total.update(labels)

    print(
        f"{file_path.name}: "
        f"Normal = {labels.get(0, 0)}, "
        f"Sybil = {labels.get(1, 0)}"
    )

print("\n===== TOTAL =====")
print(f"Normal: {total.get(0, 0)}")
print(f"Sybil: {total.get(1, 0)}")
print(f"Total: {sum(total.values())}")
