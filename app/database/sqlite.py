from pathlib import Path
import sqlite3
from typing import Any

from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.tracing import tracer


logger = get_logger(__name__)


class SQLiteClient:
    """Read-only client for the manufacturing MES SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

        logger.info(
            "SQLite client initialized",
            extra={"database_path": str(self.database_path)},
        )

    def connect(self) -> sqlite3.Connection:
        """Create a read-only SQLite connection."""

        with tracer.start_as_current_span(
            "database.sqlite.connect"
        ) as span:

            span.set_attribute(
                "db.system",
                "sqlite",
            )

            logger.debug(
                "Opening read-only SQLite connection"
            )

            connection = sqlite3.connect(
                f"file:{self.database_path.resolve()}?mode=ro",
                uri=True,
            )

            connection.row_factory = sqlite3.Row

            return connection

    def list_tables(self) -> list[str]:
        """Return all user tables in the database."""

        with tracer.start_as_current_span(
            "database.sqlite.list_tables"
        ) as span:

            metrics.increment("sql_operations_total")

            with metrics.timer("sql_operation_duration_ms"):
                try:
                    with self.connect() as connection:
                        cursor = connection.execute(
                            """
                            SELECT name
                            FROM sqlite_master
                            WHERE type = 'table'
                            ORDER BY name
                            """
                        )

                        tables = [
                            row["name"]
                            for row in cursor.fetchall()
                        ]

                    metrics.increment(
                        "sql_operations_success_total"
                    )

                    span.set_attribute(
                        "db.table_count",
                        len(tables),
                    )

                    logger.info(
                        "SQLite tables retrieved",
                        extra={
                            "table_count": len(tables),
                        },
                    )

                    return tables

                except Exception:
                    metrics.increment(
                        "sql_operations_failed_total"
                    )

                    logger.exception(
                        "Failed to retrieve SQLite tables"
                    )

                    raise

    def get_table_columns(
        self,
        table_name: str,
    ) -> list[dict[str, Any]]:
        """Return SQLite column metadata for a table."""

        with tracer.start_as_current_span(
            "database.sqlite.get_table_columns"
        ) as span:

            span.set_attribute(
                "db.table",
                table_name,
            )

            logger.debug(
                "Retrieving SQLite column metadata",
                extra={"table_name": table_name},
            )

            with self.connect() as connection:
                cursor = connection.execute(
                    f'PRAGMA table_info("{table_name}")'
                )

                rows = [
                    dict(row)
                    for row in cursor.fetchall()
                ]

            span.set_attribute(
                "db.column_count",
                len(rows),
            )

            return rows

    def get_foreign_keys(
        self,
        table_name: str,
    ) -> list[dict[str, Any]]:
        """Return SQLite foreign-key metadata for a table."""

        with tracer.start_as_current_span(
            "database.sqlite.get_foreign_keys"
        ) as span:

            span.set_attribute(
                "db.table",
                table_name,
            )

            logger.debug(
                "Retrieving SQLite foreign-key metadata",
                extra={"table_name": table_name},
            )

            with self.connect() as connection:
                cursor = connection.execute(
                    f'PRAGMA foreign_key_list("{table_name}")'
                )

                rows = [
                    dict(row)
                    for row in cursor.fetchall()
                ]

            span.set_attribute(
                "db.foreign_key_count",
                len(rows),
            )

            return rows

    def execute_read_only(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        """Execute a read-only SELECT query."""

        normalized_query = query.strip().lower()

        if not normalized_query.startswith("select"):
            logger.warning(
                "Rejected non-SELECT SQL query"
            )

            raise ValueError(
                "Only SELECT queries are allowed."
            )

        with tracer.start_as_current_span(
            "database.sqlite.execute_read_only"
        ) as span:

            span.set_attribute(
                "db.system",
                "sqlite",
            )

            span.set_attribute(
                "db.operation",
                "SELECT",
            )

            metrics.increment("sql_queries_total")

            with metrics.timer("sql_query_duration_ms"):
                try:
                    with self.connect() as connection:
                        cursor = connection.execute(
                            query,
                            parameters,
                        )

                        rows = [
                            dict(row)
                            for row in cursor.fetchall()
                        ]

                    metrics.increment(
                        "sql_queries_success_total"
                    )

                    span.set_attribute(
                        "db.row_count",
                        len(rows),
                    )

                    logger.info(
                        "Read-only SQL query completed",
                        extra={
                            "row_count": len(rows),
                        },
                    )

                    return rows

                except Exception:
                    metrics.increment(
                        "sql_queries_failed_total"
                    )

                    logger.exception(
                        "Read-only SQL query failed"
                    )

                    raise