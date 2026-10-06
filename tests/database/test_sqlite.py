from pathlib import Path

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

    try:
        client.execute_read_only("DELETE FROM Machines")
        assert False, "DELETE query should have been rejected"
    except ValueError as exc:
        assert "SELECT" in str(exc)