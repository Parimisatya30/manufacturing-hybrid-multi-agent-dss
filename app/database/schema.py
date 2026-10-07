from dataclasses import dataclass, field
from typing import Any

from app.database.sqlite import SQLiteClient
from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.tracing import tracer


logger = get_logger(__name__)


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    data_type: str
    not_null: bool
    default_value: Any
    primary_key: bool


@dataclass
class ForeignKeyInfo:
    """Information about a foreign-key relationship."""

    column: str
    referenced_table: str
    referenced_column: str


@dataclass
class TableInfo:
    """Metadata describing a database table."""

    name: str
    columns: list[ColumnInfo] = field(
        default_factory=list
    )
    foreign_keys: list[ForeignKeyInfo] = field(
        default_factory=list
    )
    row_count: int = 0


class SchemaProfiler:
    """Inspect the structure of the MES SQLite database."""

    def __init__(self, database: SQLiteClient) -> None:
        self.database = database

    def profile_table(
        self,
        table_name: str,
    ) -> TableInfo:
        """Return metadata for a single table."""

        with tracer.start_as_current_span(
            "database.schema.profile_table"
        ) as span:

            span.set_attribute(
                "db.table",
                table_name,
            )

            logger.info(
                "Profiling database table",
                extra={
                    "table_name": table_name,
                },
            )

            metrics.increment(
                "schema_profile_tables_total"
            )

            try:
                with metrics.timer(
                    "schema_profile_duration_ms"
                ):
                    columns = self._get_columns(
                        table_name
                    )

                    foreign_keys = self._get_foreign_keys(
                        table_name
                    )

                    row_count = self._get_row_count(
                        table_name
                    )

                metrics.increment(
                    "schema_profile_tables_success_total"
                )

                span.set_attribute(
                    "db.column_count",
                    len(columns),
                )

                span.set_attribute(
                    "db.foreign_key_count",
                    len(foreign_keys),
                )

                span.set_attribute(
                    "db.row_count",
                    row_count,
                )

                return TableInfo(
                    name=table_name,
                    columns=columns,
                    foreign_keys=foreign_keys,
                    row_count=row_count,
                )

            except Exception as exc:
                span.record_exception(exc)
                span.set_status(
                    trace.Status(
                        trace.StatusCode.ERROR,
                        str(exc),
                    )
                )

                logger.exception(
                    "Failed to profile database table",
                    extra={
                        "table_name": table_name,
                    },
                )

                raise

    def profile_database(
        self,
    ) -> list[TableInfo]:
        """Profile all user tables in the database."""

        with tracer.start_as_current_span(
            "database.schema.profile"
        ) as span:

            try:
                tables = self.database.list_tables()

                span.set_attribute(
                    "db.table_count",
                    len(tables),
                )

                logger.info(
                    "Profiling database schema",
                    extra={
                        "table_count": len(tables),
                    },
                )

                result = [
                    self.profile_table(table_name)
                    for table_name in tables
                ]

                span.set_attribute(
                    "db.profiled_table_count",
                    len(result),
                )

                return result

            except Exception as exc:
                span.record_exception(exc)
                span.set_status(
                    trace.Status(
                        trace.StatusCode.ERROR,
                        str(exc),
                    )
                )

                logger.exception(
                    "Failed to profile database schema"
                )

                raise

    def _get_columns(
        self,
        table_name: str,
    ) -> list[ColumnInfo]:
        """Retrieve column metadata for a table."""

        rows = self.database.get_table_columns(
            table_name
        )

        return [
            ColumnInfo(
                name=row["name"],
                data_type=row["type"],
                not_null=bool(row["notnull"]),
                default_value=row["dflt_value"],
                primary_key=bool(row["pk"]),
            )
            for row in rows
        ]

    def _get_foreign_keys(
        self,
        table_name: str,
    ) -> list[ForeignKeyInfo]:
        """Retrieve foreign-key relationships for a table."""

        rows = self.database.get_foreign_keys(
            table_name
        )

        return [
            ForeignKeyInfo(
                column=row["from"],
                referenced_table=row["table"],
                referenced_column=row["to"],
            )
            for row in rows
        ]

    def _get_row_count(
        self,
        table_name: str,
    ) -> int:
        """Return the number of rows in a table."""

        rows = self.database.execute_read_only(
            f'SELECT COUNT(*) AS row_count FROM "{table_name}"'
        )

        return int(rows[0]["row_count"])