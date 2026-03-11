from pathlib import Path
import sqlite3

from app.db.connection import get_connection


def initialize_database() -> None:
    schema_path = Path(__file__).resolve().parent / "schema.sql"

    with open(schema_path, "r", encoding="utf-8") as file:
        schema_sql = file.read()

    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        seed_reference_data(conn)
        conn.commit()
    finally:
        conn.close()


def seed_reference_data(conn: sqlite3.Connection) -> None:
    algorithms = [
        ("AES-256-CBC", "symmetric", "Symmetric encryption with AES-256 in CBC mode."),
        ("RSA", "asymmetric", "Asymmetric encryption using RSA key pair."),
    ]

    frameworks = [
        ("OpenSSL", "CLI", "Used via command line and subprocess."),
        ("PyCryptodome", "Python package", "Alternative Python cryptography framework."),
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO algorithms (name, type, description)
        VALUES (?, ?, ?)
        """,
        algorithms
    )

    conn.executemany(
        """
        INSERT OR IGNORE INTO frameworks (name, version, notes)
        VALUES (?, ?, ?)
        """,
        frameworks
    )