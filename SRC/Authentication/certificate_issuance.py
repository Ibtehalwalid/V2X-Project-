import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .key_generation import (
    generate_ecdsa_private_key,
    save_private_key,
    load_private_key
)


def load_registered_vehicles(registry_path):

    with open(registry_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data["registered_vehicles"])


def create_or_load_ca(private_key_path, certificate_path, password):

    private_key_path = Path(private_key_path)
    certificate_path = Path(certificate_path)

    key_exists = private_key_path.exists()
    cert_exists = certificate_path.exists()

    if key_exists != cert_exists:
        raise RuntimeError(
            "CA private key and certificate are incomplete."
        )

    if key_exists:

        ca_private_key = load_private_key(
            private_key_path,
            password
        )

        ca_certificate = x509.load_pem_x509_certificate(
            certificate_path.read_bytes()
        )

        if (
            ca_private_key.public_key().public_numbers()
            != ca_certificate.public_key().public_numbers()
        ):
            raise ValueError("CA key and certificate do not match.")

        return ca_private_key, ca_certificate

    ca_private_key = generate_ecdsa_private_key()

    subject = x509.Name([
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            "V2X Root CA"
        )
    ])

    now = datetime.now(timezone.utc)

    ca_certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(ca_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(
            x509.BasicConstraints(
                ca=True,
                path_length=0
            ),
            critical=True
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=None,
                decipher_only=None
            ),
            critical=True
        )
        .sign(ca_private_key, hashes.SHA256())
    )

    save_private_key(
        ca_private_key,
        private_key_path,
        password
    )

    certificate_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    certificate_path.write_bytes(
        ca_certificate.public_bytes(
            serialization.Encoding.PEM
        )
    )

    return ca_private_key, ca_certificate


def create_vehicle_csr(vehicle_id, vehicle_private_key):

    subject = x509.Name([
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            vehicle_id
        )
    ])

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
        .sign(vehicle_private_key, hashes.SHA256())
    )

    return csr


def issue_vehicle_certificate(
    vehicle_id,
    csr,
    registered_vehicles,
    ca_private_key,
    ca_certificate
):

    if vehicle_id not in registered_vehicles:
        raise ValueError(
            f"{vehicle_id} is not registered."
        )

    if not csr.is_signature_valid:
        raise ValueError("Invalid CSR signature.")

    common_names = csr.subject.get_attributes_for_oid(
        NameOID.COMMON_NAME
    )

    if len(common_names) != 1:
        raise ValueError("Invalid CSR identity.")

    if common_names[0].value != vehicle_id:
        raise ValueError("CSR identity mismatch.")

    vehicle_public_key = csr.public_key()

    if not isinstance(vehicle_public_key, ec.EllipticCurvePublicKey):
        raise ValueError("Vehicle key must use ECDSA.")

    if vehicle_public_key.curve.name != "secp256r1":
        raise ValueError("Vehicle must use P-256.")

    now = datetime.now(timezone.utc)

    certificate = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_certificate.subject)
        .public_key(vehicle_public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(
                ca=False,
                path_length=None
            ),
            critical=True
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=None,
                decipher_only=None
            ),
            critical=True
        )
        .sign(ca_private_key, hashes.SHA256())
    )

    return certificate


def save_certificate(certificate, file_path):

    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path.write_bytes(
        certificate.public_bytes(
            serialization.Encoding.PEM
        )
    )


def load_certificate(file_path):

    return x509.load_pem_x509_certificate(
        Path(file_path).read_bytes()
    )
