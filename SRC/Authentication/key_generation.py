from pathlib import Path 
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate_ecdsa_private_key():

    return ec.generate_private_key(
        ec.SECP256R1()
    )


def save_private_key(private_key, file_path, password):

    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    encrypted_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            password.encode("utf-8")
        )
    )

    file_path.write_bytes(encrypted_key)


def load_private_key(file_path, password):

    file_path = Path(file_path)

    return serialization.load_pem_private_key(
        file_path.read_bytes(),
        password=password.encode("utf-8")
    )


def get_public_key(private_key):

    return private_key.public_key()

def get_or_create_vehicle_key(vehicle_id, key_directory, password):
    key_file = Path(key_directory) / vehicle_id / "private_key.pem"

    if key_file.exists():
        print(f"[INFO] Loading existing key for {vehicle_id}")
        return load_private_key(key_file, password)

    print(f"[INFO] No existing key found for {vehicle_id}")
    print(f"[INFO] Generating a new key for {vehicle_id}")

    private_key = generate_ecdsa_private_key()
    save_private_key(private_key, key_file, password)

    return private_key