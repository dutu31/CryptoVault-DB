import sqlite3

from app.config import DB_PATH, ensure_directories


def get_connection() -> sqlite3.Connection:
    ensure_directories()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn