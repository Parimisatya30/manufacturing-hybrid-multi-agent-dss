from pathlib import Path
from typing import Any

from app.database.sqlite import SQLiteClient


class SQLTool:
    """DSS tool for executing validated read-only SQL queries."""

    def __init__(self, database_path: str | Path) -> None:
        self.client = SQLiteClient(database_path)

    def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        """Execute a read-only SQL query against the MES database."""

        return self.client.execute_read_only(
            query=query,
            parameters=parameters,
        )