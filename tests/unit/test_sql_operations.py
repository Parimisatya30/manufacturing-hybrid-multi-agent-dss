from unittest.mock import MagicMock

import pytest

from app.router.sql_operations import SQLOperationRegistry


@pytest.fixture
def sql_tool():
    return MagicMock()


@pytest.fixture
def registry(sql_tool):
    return SQLOperationRegistry(sql_tool)


def test_get_machine_details_uses_parameterized_query(registry, sql_tool):
    sql_tool.execute.return_value = [{"MachineID": 8}]

    result = registry.get_machine_details(8)

    assert result == [{"MachineID": 8}]
    sql_tool.execute.assert_called_once()
    query, parameters = sql_tool.execute.call_args.args
    assert "WHERE MachineID = ?" in query
    assert parameters == (8,)


def test_list_machines_executes_query(registry, sql_tool):
    sql_tool.execute.return_value = [{"MachineID": 1}]

    result = registry.list_machines()

    assert result == [{"MachineID": 1}]
    sql_tool.execute.assert_called_once()
    assert "FROM Machines" in sql_tool.execute.call_args.args[0]


def test_get_work_orders_executes_query(registry, sql_tool):
    sql_tool.execute.return_value = [{"OrderID": 100}]

    result = registry.get_work_orders()

    assert result == [{"OrderID": 100}]
    sql_tool.execute.assert_called_once()
    query = sql_tool.execute.call_args.args[0]
    assert "FROM WorkOrders" in query
    assert "OrderID" in query
    assert "LIMIT 100" in query


@pytest.mark.parametrize("machine_id", [0, -1])
def test_get_machine_details_rejects_nonpositive_id(registry, machine_id):
    with pytest.raises(ValueError, match="positive"):
        registry.get_machine_details(machine_id)


@pytest.mark.parametrize("machine_id", [True, 8.0, "8"])
def test_get_machine_details_rejects_non_integer_id(registry, machine_id):
    with pytest.raises(TypeError, match="integer"):
        registry.get_machine_details(machine_id)


def test_operations_returns_approved_operations(registry):
    operations = registry.operations()

    assert set(operations) == {
        "get_machine_details",
        "list_machines",
        "get_work_orders",
    }