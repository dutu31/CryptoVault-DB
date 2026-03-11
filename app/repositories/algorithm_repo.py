from app.db.connection import get_connection
from app.models.entities import Algorithm


class AlgorithmRepository:
    def get_all(self) -> list[Algorithm]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, name, type, description, is_active
                FROM algorithms
                ORDER BY id
                """
            ).fetchall()

            return [
                Algorithm(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    description=row["description"],
                    is_active=row["is_active"],
                )
                for row in rows
            ]
        finally:
            conn.close()