from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "database"
KEYS_DIR = DATA_DIR / "keys"
INPUT_FILES_DIR = DATA_DIR / "input_files"
OUTPUT_FILES_DIR = DATA_DIR / "output_files"

DB_PATH = DATABASE_DIR / "crypto_manager.db"


def ensure_directories() -> None:
    directories = [
        DATA_DIR,
        DATABASE_DIR,
        KEYS_DIR,
        INPUT_FILES_DIR,
        OUTPUT_FILES_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)