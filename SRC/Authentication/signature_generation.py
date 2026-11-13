import base64
import binascii
import json
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

SIGNATURE_ALGORITHM = "ECDSA-P256-SHA256"


def serialize_beacon(beacon):

    if not isinstance(beacon, dict):
        raise TypeError("Beacon must be a dictionary.")

    beacon_bytes = json.dumps(
        beacon,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    ).encode("utf-8")

    return beacon_bytes


def sign_beacon(beacon, private_key):

    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise TypeError("Private key must use ECDSA.")

    if private_key.curve.name != "secp256r1":
        raise ValueError("Private key must use P-256.")

    beacon_bytes = serialize_beacon(beacon)

    signature = private_key.sign(
        beacon_bytes,
        ec.ECDSA(hashes.SHA256())
    )

    return base64.b64encode(signature).decode("ascii")


def create_signed_packet(
    vehicle_id,
    beacon,
    private_key,
    certificate
):

    common_names = certificate.subject.get_attributes_for_oid(
        NameOID.COMMON_NAME
    )

    if len(common_names) != 1:
        raise ValueError("Invalid vehicle certificate identity.")

    if common_names[0].value != vehicle_id:
        raise ValueError("Certificate identity does not match vehicle ID.")

    certificate_public_key = certificate.public_key()

    if not isinstance(certificate_public_key, ec.EllipticCurvePublicKey):
        raise ValueError("Certificate must contain an ECDSA public key.")

    if certificate_public_key.curve.name != "secp256r1":
        raise ValueError("Certificate must use P-256.")

    if (
        private_key.public_key().public_numbers()
        != certificate_public_key.public_numbers()
    ):
        raise ValueError("Private key does not match vehicle certificate.")

    signature = sign_beacon(beacon, private_key)

    signed_packet = {
        "vehicle_id": vehicle_id,
        "beacon": beacon,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "signature": signature,
        "certificate_pem": certificate.public_bytes(
            serialization.Encoding.PEM
        ).decode("ascii")
    }

    return signed_packet


def verify_beacon_signature(packet):

    if not isinstance(packet, dict):
        return False

    try:
        if packet["signature_algorithm"] != SIGNATURE_ALGORITHM:
            return False

        vehicle_id = packet["vehicle_id"]
        beacon = packet["beacon"]

        if not isinstance(vehicle_id, str):
            return False

        certificate_pem = packet["certificate_pem"].encode("ascii")

        certificate = x509.load_pem_x509_certificate(
            certificate_pem
        )

        common_names = certificate.subject.get_attributes_for_oid(
            NameOID.COMMON_NAME
        )

        if len(common_names) != 1:
            return False

        if common_names[0].value != vehicle_id:
            return False

        public_key = certificate.public_key()

        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            return False

        if public_key.curve.name != "secp256r1":
            return False

        beacon_bytes = serialize_beacon(beacon)

        signature = base64.b64decode(
            packet["signature"],
            validate=True
        )

        public_key.verify(
            signature,
            beacon_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        return True

    except (
        InvalidSignature,
        ValueError,
        TypeError,
        KeyError,
        binascii.Error,
        UnicodeError
    ):
        return False
