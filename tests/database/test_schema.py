from pathlib import Path

from app.database.schema import SchemaProfiler
from app.database.sqlite import SQLiteClient


DATABASE_PATH = Path("data/raw/MES.db")


def test_profile_machines_table() -> None:
    database = SQLiteClient(DATABASE_PATH)
    profiler = SchemaProfiler(database)

    table = profiler.profile_table("Machines")

    assert table.name == "Machines"
    assert table.row_count > 0

    column_names = {column.name for column in table.columns}

    assert "MachineID" in column_names
    assert "Name" in column_names
    assert "Status" in column_names


def test_machine_primary_key() -> None:
    database = SQLiteClient(DATABASE_PATH)
    profiler = SchemaProfiler(database)

    table = profiler.profile_table("Machines")

    primary_keys = {
        column.name
        for column in table.columns
        if column.primary_key
    }

    assert "MachineID" in primary_keys


def test_machine_foreign_key() -> None:
    database = SQLiteClient(DATABASE_PATH)
    profiler = SchemaProfiler(database)

    table = profiler.profile_table("Machines")

    relationships = {
        (
            foreign_key.column,
            foreign_key.referenced_table,
            foreign_key.referenced_column,
        )
        for foreign_key in table.foreign_keys
    }

    assert (
        "WorkCenterID",
        "WorkCenters",
        "WorkCenterID",
    ) in relationships


def test_profile_database() -> None:
    database = SQLiteClient(DATABASE_PATH)
    profiler = SchemaProfiler(database)

    tables = profiler.profile_database()

    table_names = {table.name for table in tables}

    assert "Machines" in table_names
    assert "WorkCenters" in table_names
    assert "WorkOrders" in table_names
    assert "QualityControl" in table_names