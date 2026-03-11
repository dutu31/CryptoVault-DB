import hashlib
from pathlib import Path


def compute_sha256(file_path: str | Path) -> str:
    file_path = Path(file_path)

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()