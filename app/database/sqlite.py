from pathlib import Path
import sqlite3
from typing import Any


class SQLiteClient:
    """Read-only client for the manufacturing MES SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

    def connect(self) -> sqlite3.Connection:
        """Create a read-only SQLite connection."""
        connection = sqlite3.connect(
            f"file:{self.database_path.resolve()}?mode=ro",
            uri=True,
        )

        connection.row_factory = sqlite3.Row
        return connection

    def list_tables(self) -> list[str]:
        """Return all user tables in the database."""
        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            )

            return [row["name"] for row in cursor.fetchall()]

    def execute_read_only(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        """Execute a read-only SELECT query."""

        normalized_query = query.strip().lower()

        if not normalized_query.startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

        with self.connect() as connection:
            cursor = connection.execute(query, parameters)

            return [dict(row) for row in cursor.fetchall()]