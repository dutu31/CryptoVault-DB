from app.db.connection import get_connection
from app.models.entities import Framework


class FrameworkRepository:
    def get_all(self) -> list[Framework]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, name, version, notes
                FROM frameworks
                ORDER BY id
                """
            ).fetchall()

            return [
                Framework(
                    id=row["id"],
                    name=row["name"],
                    version=row["version"],
                    notes=row["notes"],
                )
                for row in rows
            ]
        finally:
            conn.close()