import os
import json
import glob
import pandas as pd

# ==================== Settings ====================
INPUT_FOLDER = r"E:\FCI SADAT ACADEMY\Graduation Project\Datasets\InTAS_urban_2_trafficCongestionSybil Dataset\InTAS_urban_2_trafficCongestionSybil\Test\InTAS_urban_2_trafficCongestionSybil"   # ← Put the folder path here
OUTPUT_CSV = "Test_15,500 Messages.csv"
TARGET_MESSAGES = 15500
# ==================================================

def extract_xyz(value):
    """Extract x, y, z from a comma-separated string like 'x,y,z' """
    if value is None:
        return None, None, None

    # If it's a string in the form "x,y,z"
    if isinstance(value, str):
        try:
            parts = [p.strip() for p in value.split(",")]
            if len(parts) >= 3:
                return float(parts[0]), float(parts[1]), float(parts[2])
        except:
            return None, None, None

    # If it's a list or tuple (fallback)
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return value[0], value[1], value[2]

    # If it's a dict
    if isinstance(value, dict):
        return value.get("x"), value.get("y"), value.get("z")

    return None, None, None

def flatten_message(msg, source_file):
    """Convert nested message dict into a flat row with desired column order"""
    receiver = msg.get("receiver", {}) or {}
    sender = msg.get("sender", {}) or {}

    # Receiver position (x, y, z)
    rx, ry, rz = extract_xyz(receiver.get("pos"))
    rnx, rny, rnz = extract_xyz(receiver.get("pos_noise"))

    # Sender position (x, y, z)
    sx, sy, sz = extract_xyz(sender.get("pos"))
    snx, sny, snz = extract_xyz(sender.get("pos_noise"))

    flat = {
        "rcvTime": msg.get("rcvTime"),
        "sendTime": msg.get("sendTime"),
        "sender_id": msg.get("sender_id"),
        "sender_alias": msg.get("sender_alias"),
        "messageID": msg.get("messageID"),
        "attacker": msg.get("attacker"),

        # Receiver data
        "receiver_pos_x": rx,
        "receiver_pos_y": ry,
        "receiver_pos_z": rz,
        "receiver_pos_noise_x": rnx,
        "receiver_pos_noise_y": rny,
        "receiver_pos_noise_z": rnz,
        "receiver_spd": receiver.get("spd"),
        "receiver_spd_noise": receiver.get("spd_noise"),
        "receiver_acl": receiver.get("acl"),
        "receiver_acl_noise": receiver.get("acl_noise"),
        "receiver_hed": receiver.get("hed"),
        "receiver_hed_noise": receiver.get("hed_noise"),
        "receiver_driversProfile": receiver.get("driversProfile"),

        # Sender data
        "sender_pos_x": sx,
        "sender_pos_y": sy,
        "sender_pos_z": sz,
        "sender_pos_noise_x": snx,
        "sender_pos_noise_y": sny,
        "sender_pos_noise_z": snz,
        "sender_spd": sender.get("spd"),
        "sender_spd_noise": sender.get("spd_noise"),
        "sender_acl": sender.get("acl"),
        "sender_acl_noise": sender.get("acl_noise"),
        "sender_hed": sender.get("hed"),
        "sender_hed_noise": sender.get("hed_noise"),
        "sender_driversProfile": sender.get("driversProfile"),
        "sender_distance_to_road_edge": sender.get("distance_to_road_edge"),

        "source_file": source_file,
    }
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
    print(f"\nColumns order:\n{list(df.columns)}")

if __name__ == "__main__":
    main()