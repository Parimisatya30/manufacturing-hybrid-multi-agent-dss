from pathlib import Path

from app.tools.sql_tool import SQLTool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "raw" / "MES.db"


def test_sql_tool_can_execute_select():
    tool = SQLTool(DATABASE_PATH)

    results = tool.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )

    assert len(results) > 0


def test_sql_tool_returns_dictionaries():
    tool = SQLTool(DATABASE_PATH)

    results = tool.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )

    assert isinstance(results, list)
    assert isinstance(results[0], dict)


def test_sql_tool_can_query_machine_data():
    tool = SQLTool(DATABASE_PATH)

    results = tool.execute(
        "SELECT * FROM Machines LIMIT 5"
    )

    assert len(results) <= 5
    assert all(isinstance(row, dict) for row in results)

def test_sql_tool_can_query_running_machines():
    tool = SQLTool(DATABASE_PATH)

    results = tool.execute(
        """
        SELECT MachineID, Name, Status
        FROM Machines
        WHERE Status = 'running'
        """
    )

    assert len(results) > 0
    assert all(row["Status"] == "running" for row in results)