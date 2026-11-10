import os
import json
import glob
import pandas as pd

# ==================== Settings ====================
INPUT_FOLDER = "E:\FCI SADAT ACADEMY\Graduation Project\Datasets\InTAS_urban_2_trafficCongestionSybil Dataset\InTAS_urban_2_trafficCongestionSybil\Test\InTAS_urban_2_trafficCongestionSybil"   # ← حطي هنا مسار الفولدر
OUTPUT_CSV = "Test_15,500 Messages.csv"
TARGET_MESSAGES = 15500
# ==================================================

def flatten_message(msg, source_file):
    """Convert nested message dict into a flat row + source file name"""
    flat = {
        "source_file": source_file,
        "rcvTime": msg.get("rcvTime"),
        "sendTime": msg.get("sendTime"),
        "sender_id": msg.get("sender_id"),
        "sender_alias": msg.get("sender_alias"),
        "messageID": msg.get("messageID"),
        "attacker": msg.get("attacker"),
    }

    # Receiver data
    receiver = msg.get("receiver", {})
    flat.update({
        "receiver_pos": receiver.get("pos"),
        "receiver_pos_noise": receiver.get("pos_noise"),
        "receiver_spd": receiver.get("spd"),
        "receiver_spd_noise": receiver.get("spd_noise"),
        "receiver_acl": receiver.get("acl"),
        "receiver_acl_noise": receiver.get("acl_noise"),
        "receiver_hed": receiver.get("hed"),
        "receiver_hed_noise": receiver.get("hed_noise"),
        "receiver_driversProfile": receiver.get("driversProfile"),
    })

    # Sender data
    sender = msg.get("sender", {})
    flat.update({
        "sender_pos": sender.get("pos"),
        "sender_pos_noise": sender.get("pos_noise"),
        "sender_spd": sender.get("spd"),
        "sender_spd_noise": sender.get("spd_noise"),
        "sender_acl": sender.get("acl"),
        "sender_acl_noise": sender.get("acl_noise"),
        "sender_hed": sender.get("hed"),
        "sender_hed_noise": sender.get("hed_noise"),
        "sender_driversProfile": sender.get("driversProfile"),
        "sender_distance_to_road_edge": sender.get("distance_to_road_edge"),
    })

    return flat

def main():
    all_messages = []
    json_files = sorted(glob.glob(os.path.join(INPUT_FOLDER, "*.json")))

    print(f"Found {len(json_files)} JSON files\n")

    for file_path in json_files:
        if len(all_messages) >= TARGET_MESSAGES:
            break

        file_name = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"Skipped {file_name} (not a list)")
                continue

            for msg in data:
                all_messages.append(flatten_message(msg, file_name))
                if len(all_messages) >= TARGET_MESSAGES:
                    break

            print(f"✓ {file_name} → Current total: {len(all_messages)}")

        except Exception as e:
            print(f"✗ Error in {file_name}: {e}")

    print(f"\n{'='*50}")
    print(f"Total collected messages: {len(all_messages)}")

    # Convert to DataFrame and save
    df = pd.DataFrame(all_messages)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"Saved to: {OUTPUT_CSV}")
    print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
    print(f"\nFirst 5 columns: {list(df.columns[:5])}")

if __name__ == "__main__":
    main()