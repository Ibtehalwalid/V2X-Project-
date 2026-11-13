
import json
import time
import base64
import statistics

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding


# =========================
# BENCHMARK CONFIGURATION
# =========================

KEY_GENERATION_ITERATIONS = 10
SIGNING_ITERATIONS = 500

OUTPUT_FILE = Path(__file__).resolve().parent / "benchmark_results.json"


# =========================
# SAMPLE BEACON
# =========================

beacon = {
    "sender_id": "Vehicle_A",
    "messageID": 101,
    "sendTime": 1250.5,
    "sender": {
        "pos": [10.2, 20.5],
        "spd": [15.0, 0.0],
        "acl": [0.2, 0.0],
        "hed": 1.57
    }
}


def serialize_beacon(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    ).encode("utf-8")


message = serialize_beacon(beacon)


# =========================
# KEY GENERATION
# =========================

def generate_rsa_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072
    )


def generate_ecdsa_key():
    return ec.generate_private_key(
        ec.SECP256R1()
    )


def benchmark_key_generation(key_generator):
    execution_times = []
    private_key = None

    for _ in range(KEY_GENERATION_ITERATIONS):
        start = time.perf_counter()

        private_key = key_generator()

        end = time.perf_counter()
        execution_times.append((end - start) * 1000)

    return private_key, execution_times


# =========================
# DIGITAL SIGNING
# =========================

def sign_rsa(private_key, message):
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )


def sign_ecdsa(private_key, message):
    return private_key.sign(
        message,
        ec.ECDSA(hashes.SHA256())
    )


def benchmark_signing(private_key, signing_function):
    execution_times = []
    signatures = []

    for _ in range(SIGNING_ITERATIONS):
        start = time.perf_counter()

        signature = signing_function(private_key, message)

        end = time.perf_counter()

        execution_times.append((end - start) * 1000)
        signatures.append(signature)

    return execution_times, signatures


# =========================
# KEY AND CERTIFICATE SIZES
# =========================

def get_key_sizes(private_key):

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return len(private_key_pem), len(public_key_pem)


def generate_self_signed_certificate(private_key, common_name):

    subject = x509.Name([
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            common_name
        )
    ])

    now = datetime.now(timezone.utc)

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        )
        .sign(private_key, hashes.SHA256())
    )

    return certificate


# =========================
# SIGNED PACKET SIZE
# =========================

def calculate_packet_sizes(signatures, certificate, algorithm_name):

    certificate_pem = certificate.public_bytes(
        serialization.Encoding.PEM
    ).decode("utf-8")

    packet_sizes = []

    for signature in signatures:

        packet = {
            "vehicle_id": "Vehicle_A",
            "beacon": beacon,
            "signature_algorithm": algorithm_name,
            "signature": base64.b64encode(signature).decode("ascii"),
            "certificate_pem": certificate_pem
        }

        packet_bytes = json.dumps(
            packet,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False
        ).encode("utf-8")

        packet_sizes.append(len(packet_bytes))

    return packet_sizes


# =========================
# RUN ONE ALGORITHM
# =========================

def run_benchmark(name, key_generator, signing_function):

    print(f"\nRunning {name} benchmark...")

    private_key, keygen_times = benchmark_key_generation(
        key_generator
    )

    signing_times, signatures = benchmark_signing(
        private_key,
        signing_function
    )

    private_key_size, public_key_size = get_key_sizes(
        private_key
    )

    certificate = generate_self_signed_certificate(
        private_key,
        "Vehicle_A"
    )

    certificate_pem = certificate.public_bytes(
        serialization.Encoding.PEM
    )

    packet_sizes = calculate_packet_sizes(
        signatures,
        certificate,
        name
    )

    return {
        "algorithm": name,

        "key_generation_avg_ms": statistics.mean(keygen_times),
        "key_generation_median_ms": statistics.median(keygen_times),

        "signing_avg_ms": statistics.mean(signing_times),
        "signing_median_ms": statistics.median(signing_times),

        "signature_avg_bytes": statistics.mean(
            len(signature) for signature in signatures
        ),

        "signature_median_bytes": statistics.median(
            len(signature) for signature in signatures
        ),

        "private_key_size_bytes": private_key_size,
        "public_key_size_bytes": public_key_size,
        "certificate_size_bytes": len(certificate_pem),

        "signed_packet_avg_bytes": statistics.mean(packet_sizes),
        "signed_packet_median_bytes": statistics.median(packet_sizes)
    }


# =========================
# MAIN
# =========================

def main():

    results = []

    results.append(
        run_benchmark(
            "RSA-3072-PSS-SHA256",
            generate_rsa_key,
            sign_rsa
        )
    )

    results.append(
        run_benchmark(
            "ECDSA-P256-SHA256",
            generate_ecdsa_key,
            sign_ecdsa
        )
    )

    print("\n========== BENCHMARK RESULTS ==========")

    for result in results:

        print(f"\n{result['algorithm']}")

        for metric, value in result.items():

            if metric != "algorithm":
                print(f"{metric}: {value:.3f}" if isinstance(value, float)
                      else f"{metric}: {value}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
