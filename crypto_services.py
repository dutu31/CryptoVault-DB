import datetime
import hashlib
import json
import secrets
import subprocess
import tempfile
import time
import tracemalloc
import uuid
from pathlib import Path

BASE_DATA_DIR = Path("data")
ORIGINAL_DIR = BASE_DATA_DIR / "original"
ENCRYPTED_DIR = BASE_DATA_DIR / "encrypted"
DECRYPTED_DIR = BASE_DATA_DIR / "decrypted"


def ensure_data_directories():
    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)
    DECRYPTED_DIR.mkdir(parents=True, exist_ok=True)


def safe_part(value):
    value = value.replace("\\", "_").replace("/", "_").replace(":", "_")
    value = value.replace("*", "_").replace("?", "_").replace('"', "_")
    value = value.replace("<", "_").replace(">", "_").replace("|", "_")
    value = value.strip()
    return value if value else "fisier"


def unique_file_name(original_name):
    name = safe_part(original_name)
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    token = uuid.uuid4().hex[:8]
    return f"{stamp}_{token}_{name}"


def output_file_name(original_name, prefix, suffix):
    name = safe_part(original_name)
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    token = uuid.uuid4().hex[:8]
    return f"{stamp}_{token}_{prefix}_{name}{suffix}"


def sha256_file(path):
    hash_obj = hashlib.sha256()
    with open(path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def generate_aes_key():
    return secrets.token_hex(32)


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError("OpenSSL nu a fost găsit. Verifică dacă este instalat și adăugat în PATH.")

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Comanda OpenSSL a eșuat."
        raise RuntimeError(message)

    return result.stdout


def generate_rsa_key_pair_openssl(bits=2048):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        private_path = temp_path / "private_key.pem"
        public_path = temp_path / "public_key.pem"

        run_command(["openssl", "genrsa", "-out", str(private_path), str(bits)])
        run_command(["openssl", "rsa", "-in", str(private_path), "-pubout", "-out", str(public_path)])

        private_key = private_path.read_text(encoding="utf-8")
        public_key = public_path.read_text(encoding="utf-8")

    return json.dumps(
        {
            "private_key": private_key,
            "public_key": public_key,
        },
        ensure_ascii=False,
        indent=2
    )


def measure_action(action):
    tracemalloc.start()
    start_time = time.perf_counter()

    try:
        action()
    finally:
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    time_ms = (end_time - start_time) * 1000
    memory_kb = peak / 1024

    return round(time_ms, 3), round(memory_kb, 3)


def aes_key_bytes(key_value):
    return hashlib.sha256(key_value.encode("utf-8")).digest()


def pkcs7_pad(data):
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len]) * pad_len


def pkcs7_unpad(data):
    if not data:
        raise RuntimeError("Datele de decriptat sunt goale.")

    pad_len = data[-1]

    if pad_len < 1 or pad_len > 16:
        raise RuntimeError("Padding invalid la decriptare.")

    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise RuntimeError("Padding invalid la decriptare.")

    return data[:-pad_len]


def aes_pycryptodome_encrypt(input_path, output_path, key_value):
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes

    key = aes_key_bytes(key_value)
    iv = get_random_bytes(16)

    data = Path(input_path).read_bytes()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pkcs7_pad(data))

    Path(output_path).write_bytes(iv + encrypted)


def aes_pycryptodome_decrypt(input_path, output_path, key_value):
    from Crypto.Cipher import AES

    key = aes_key_bytes(key_value)
    data = Path(input_path).read_bytes()

    if len(data) < 16:
        raise RuntimeError("Fișierul criptat nu conține IV valid.")

    iv = data[:16]
    encrypted = data[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = pkcs7_unpad(cipher.decrypt(encrypted))

    Path(output_path).write_bytes(decrypted)


def aes_openssl_encrypt(input_path, output_path, key_value):
    run_command([
        "openssl",
        "enc",
        "-aes-256-cbc",
        "-pbkdf2",
        "-salt",
        "-in",
        str(input_path),
        "-out",
        str(output_path),
        "-pass",
        f"pass:{key_value}"
    ])


def aes_openssl_decrypt(input_path, output_path, key_value):
    run_command([
        "openssl",
        "enc",
        "-aes-256-cbc",
        "-pbkdf2",
        "-d",
        "-in",
        str(input_path),
        "-out",
        str(output_path),
        "-pass",
        f"pass:{key_value}"
    ])


def load_rsa_key_data(key_value):
    try:
        data = json.loads(key_value)
    except json.JSONDecodeError:
        raise RuntimeError("Cheia RSA trebuie să fie salvată în format JSON cu private_key și public_key.")

    if "private_key" not in data or "public_key" not in data:
        raise RuntimeError("Cheia RSA trebuie să conțină private_key și public_key.")

    return data


def rsa_openssl_encrypt(input_path, output_path, key_value):
    key_data = load_rsa_key_data(key_value)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        public_path = temp_path / "public_key.pem"
        public_path.write_text(key_data["public_key"], encoding="utf-8")

        run_command([
            "openssl",
            "pkeyutl",
            "-encrypt",
            "-pubin",
            "-inkey",
            str(public_path),
            "-in",
            str(input_path),
            "-out",
            str(output_path),
            "-pkeyopt",
            "rsa_padding_mode:oaep"
        ])


def rsa_openssl_decrypt(input_path, output_path, key_value):
    key_data = load_rsa_key_data(key_value)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        private_path = temp_path / "private_key.pem"
        private_path.write_text(key_data["private_key"], encoding="utf-8")

        run_command([
            "openssl",
            "pkeyutl",
            "-decrypt",
            "-inkey",
            str(private_path),
            "-in",
            str(input_path),
            "-out",
            str(output_path),
            "-pkeyopt",
            "rsa_padding_mode:oaep"
        ])


def rsa_pycryptodome_encrypt(input_path, output_path, key_value):
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.PublicKey import RSA

    key_data = load_rsa_key_data(key_value)
    public_key = RSA.import_key(key_data["public_key"].encode("utf-8"))
    cipher = PKCS1_OAEP.new(public_key)

    data = Path(input_path).read_bytes()
    max_size = public_key.size_in_bytes() - 42

    if len(data) > max_size:
        raise RuntimeError(f"Pentru RSA direct, fișierul trebuie să aibă cel mult {max_size} bytes.")

    encrypted = cipher.encrypt(data)
    Path(output_path).write_bytes(encrypted)


def rsa_pycryptodome_decrypt(input_path, output_path, key_value):
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.PublicKey import RSA

    key_data = load_rsa_key_data(key_value)
    private_key = RSA.import_key(key_data["private_key"].encode("utf-8"))
    cipher = PKCS1_OAEP.new(private_key)

    data = Path(input_path).read_bytes()
    decrypted = cipher.decrypt(data)

    Path(output_path).write_bytes(decrypted)


def run_crypto_operation(algorithm_name, framework_name, operation, input_path, output_path, key_value):
    algorithm_name = algorithm_name.lower()
    framework_name = framework_name.lower()
    operation = operation.lower()

    def action():
        if "aes" in algorithm_name and framework_name == "openssl" and operation == "encrypt":
            aes_openssl_encrypt(input_path, output_path, key_value)
            return

        if "aes" in algorithm_name and framework_name == "openssl" and operation == "decrypt":
            aes_openssl_decrypt(input_path, output_path, key_value)
            return

        if "aes" in algorithm_name and framework_name == "pycryptodome" and operation == "encrypt":
            aes_pycryptodome_encrypt(input_path, output_path, key_value)
            return

        if "aes" in algorithm_name and framework_name == "pycryptodome" and operation == "decrypt":
            aes_pycryptodome_decrypt(input_path, output_path, key_value)
            return

        if "rsa" in algorithm_name and framework_name == "openssl" and operation == "encrypt":
            rsa_openssl_encrypt(input_path, output_path, key_value)
            return

        if "rsa" in algorithm_name and framework_name == "openssl" and operation == "decrypt":
            rsa_openssl_decrypt(input_path, output_path, key_value)
            return

        if "rsa" in algorithm_name and framework_name == "pycryptodome" and operation == "encrypt":
            rsa_pycryptodome_encrypt(input_path, output_path, key_value)
            return

        if "rsa" in algorithm_name and framework_name == "pycryptodome" and operation == "decrypt":
            rsa_pycryptodome_decrypt(input_path, output_path, key_value)
            return

        raise RuntimeError("Combinația algoritm/framework/operație nu este suportată.")

    return measure_action(action)