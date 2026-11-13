import json
from pathlib import Path
from getpass import getpass
from .key_generation import (
    generate_ecdsa_private_key,
    save_private_key,
    load_private_key
)

from .certificate_issuance import (
    load_registered_vehicles,
    create_or_load_ca,
    create_vehicle_csr,
    issue_vehicle_certificate,
    save_certificate,
    load_certificate
)

from .signature_generation import (
    create_signed_packet,
    verify_beacon_signature
)


# PROJECT PATHS
ROOT = Path(__file__).resolve().parents[2]

# Registered vehicles
REGISTRY_FILE = ROOT / "Config" / "registered_vehicles.json"

# CA files
CA_KEY_FILE = (
    ROOT / "Secrets" / "pki" / "CA" / "ca_private_key.pem"
)

CA_CERT_FILE = (
    ROOT / "Certificates" / "ca_certificate.pem"
)

# Vehicle private keys
VEHICLES_KEYS_DIR = (
    ROOT / "Secrets" / "pki" / "Vehicles"
)

# Vehicle public certificates
VEHICLES_CERTS_DIR = (
    ROOT / "Certificates" / "Vehicles"
)

# Signed packet samples
SAMPLES_DIR = ROOT / "Samples"


def main():

    # 1. GET PRIVATE KEY PASSWORD

    password = getpass("Enter private key password: ")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    # 2. LOAD REGISTERED VEHICLES
    
    registered_vehicles = load_registered_vehicles(
        REGISTRY_FILE
    )

    if not registered_vehicles:
        raise ValueError("No registered vehicles found.")

    print("\nRegistered vehicles:", sorted(registered_vehicles))


    # 3. CREATE OR LOAD CERTIFICATE AUTHORITY

    ca_private_key, ca_certificate = create_or_load_ca(
        CA_KEY_FILE,
        CA_CERT_FILE,
        password
    )

    print("\nCA is ready.")

    
    # 4. GENERATE OR LOAD VEHICLE CREDENTIALS

    credentials = {}

    for vehicle_id in sorted(registered_vehicles):

        # Each vehicle gets its own folder using its actual vehicle ID.

        vehicle_key_dir = VEHICLES_KEYS_DIR / vehicle_id
        vehicle_cert_dir = VEHICLES_CERTS_DIR / vehicle_id

        # Private key path
        private_key_file = (
            vehicle_key_dir / "private_key.pem"
        )

        # Public certificate path
        certificate_file = (
            vehicle_cert_dir / "certificate.pem"
        )

        # Check existing credentials
        key_exists = private_key_file.exists()
        cert_exists = certificate_file.exists()

        if key_exists != cert_exists:
            raise RuntimeError(
                f"Incomplete credentials for {vehicle_id}."
            )

        if key_exists:

            # Load existing private key
            private_key = load_private_key(
                private_key_file,
                password
            )

            # Load existing certificate
            certificate = load_certificate(
                certificate_file
            )

            # Verify that both belong to each other
            if (
                private_key.public_key().public_numbers()
                != certificate.public_key().public_numbers()
            ):
                raise ValueError(
                    f"Vehicle key and certificate mismatch: {vehicle_id}"
                )

            print(f"Loaded existing credentials: {vehicle_id}")

        else:

            # Generate a new ECDSA private key
            private_key = generate_ecdsa_private_key()

            # Save private key locally
            save_private_key(
                private_key,
                private_key_file,
                password
            )

            # Create Certificate Signing Request
            csr = create_vehicle_csr(
                vehicle_id,
                private_key
            )

            # CA issues the vehicle certificate
            certificate = issue_vehicle_certificate(
                vehicle_id,
                csr,
                registered_vehicles,
                ca_private_key,
                ca_certificate
            )

            # Save public certificate separately
            save_certificate(
                certificate,
                certificate_file
            )

            print(f"Generated new credentials: {vehicle_id}")

        # Keep credentials available for signing
        credentials[vehicle_id] = (
            private_key,
            certificate
        )

    
    # 5. PREPARE A TEST BEACON

    vehicle_id = sorted(registered_vehicles)[0]

    private_key, certificate = credentials[vehicle_id]

    beacon = {
        "sender_id": vehicle_id,
        "sender_alias": vehicle_id,
        "messageID": 1,
        "sendTime": 100000,
        "sender": {
            "pos": [120.5, 45.2, 0.0],
            "spd": 60.0,
            "acl": 2.5,
            "hed": 90.0
        }
    }

    
    # 6. SIGN THE BEACON

    packet = create_signed_packet(
        vehicle_id,
        beacon,
        private_key,
        certificate
    )

    
    # 7. SAVE SIGNED PACKET

    SAMPLES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    packet_file = SAMPLES_DIR / "signed_packet.json"

    packet_file.write_text(
        json.dumps(packet, indent=4),
        encoding="utf-8"
    )

    
    # 8. VERIFY NORMAL PACKET

    print("\n========== NORMAL PACKET ==========")

    print(
        "Signature valid:",
        verify_beacon_signature(packet)
    )

    
    # 9. TEST TAMPERED PACKET

    tampered_packet = json.loads(
        json.dumps(packet)
    )

    tampered_packet["beacon"]["sender"]["spd"] = 150.0

    print("\n========== TAMPERED PACKET ==========")

    print(
        "Signature valid:",
        verify_beacon_signature(tampered_packet)
    )

    print("\nSigned packet saved:", packet_file)


if __name__ == "__main__":
    main()
