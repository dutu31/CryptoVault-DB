from app.db.init_db import initialize_database
from app.db.connection import get_connection


def main() -> None:
    initialize_database()

    conn = get_connection()
    try:
        algorithms_count = conn.execute(
            "SELECT COUNT(*) AS count FROM algorithms"
        ).fetchone()["count"]

        frameworks_count = conn.execute(
            "SELECT COUNT(*) AS count FROM frameworks"
        ).fetchone()["count"]

        print(f"Algorithms count: {algorithms_count}")
        print(f"Frameworks count: {frameworks_count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()   