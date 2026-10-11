
from pathlib import Path

import pytest

from app.database.sqlite import SQLiteClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "raw" / "MES.db"


def test_database_exists():
    assert DATABASE_PATH.exists()


def test_list_tables():
    client = SQLiteClient(DATABASE_PATH)

    tables = client.list_tables()

    assert len(tables) > 0
    assert all(isinstance(table, str) for table in tables)


def test_read_only_query():
    client = SQLiteClient(DATABASE_PATH)

    results = client.execute_read_only(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )

    assert len(results) > 0


def test_non_select_query_is_rejected():
    client = SQLiteClient(DATABASE_PATH)

    with pytest.raises(ValueError, match="SELECT"):
        client.execute_read_only("DELETE FROM Machines")


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "UPDATE Machines SET Status = 'stopped'",
        "DELETE FROM Machines",
        "INSERT INTO Machines (Name) VALUES ('test')",
        "DROP TABLE Machines",
    ],
)
def test_empty_or_write_query_is_rejected(query):
    client = SQLiteClient(DATABASE_PATH)

    with pytest.raises(ValueError):
        client.execute_read_only(query)


def test_multiple_sql_statements_are_rejected():
    client = SQLiteClient(DATABASE_PATH)

    with pytest.raises(ValueError):
        client.execute_read_only(
            "SELECT name FROM Machines; DELETE FROM Machines"
        )


def test_with_select_query_is_supported():
    client = SQLiteClient(DATABASE_PATH)

    results = client.execute_read_only(
        """
        WITH running_machines AS (
            SELECT MachineID, Name
            FROM Machines
            WHERE Status = ?
        )
        SELECT MachineID, Name
        FROM running_machines
        """,
        ("running",),
    )

    assert isinstance(results, list)
    assert all(isinstance(row, dict) for row in results)