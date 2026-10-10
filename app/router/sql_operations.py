
"""Approved, parameterized SQL operations for the manufacturing DSS."""

from typing import Any

from app.tools.sql_tool import SQLTool


class SQLOperationRegistry:
    """Execute a fixed set of approved, read-only SQL operations."""

    def __init__(self, sql_tool: SQLTool) -> None:
        self.sql_tool = sql_tool

    def get_machine_details(self, machine_id: int) -> list[dict[str, Any]]:
        """Retrieve details for one machine."""
        self._validate_machine_id(machine_id)

        query = """
            SELECT MachineID, Name, Type, Status,
                   LastMaintenanceDate, NextMaintenanceDate
            FROM Machines
            WHERE MachineID = ?
        """
        return self.sql_tool.execute(query, (machine_id,))

    def list_machines(self) -> list[dict[str, Any]]:
        """Retrieve machine details for all machines."""
        query = """
            SELECT MachineID, Name, Type, Status,
                   LastMaintenanceDate, NextMaintenanceDate
            FROM Machines
            ORDER BY MachineID
        """
        return self.sql_tool.execute(query)

    def get_work_orders(self) -> list[dict[str, Any]]:
        """Retrieve a bounded set of recent work orders."""
        query = """
            SELECT OrderID, ProductID, WorkCenterID, MachineID,
                   EmployeeID, Quantity, PlannedStartTime, PlannedEndTime,
                   ActualStartTime, ActualEndTime, Status, Priority,
                   LeadTime, LotNumber, ActualProduction, Scrap,
                   SetupTimeActual
            FROM WorkOrders
            ORDER BY OrderID DESC
            LIMIT 100
        """
        return self.sql_tool.execute(query)

    @staticmethod
    def _validate_machine_id(machine_id: int) -> None:
        """Reject invalid machine identifiers."""
        if isinstance(machine_id, bool) or not isinstance(machine_id, int):
            raise TypeError("machine_id must be an integer")

        if machine_id <= 0:
            raise ValueError("machine_id must be positive")

    def operations(self) -> dict[str, Any]:
        """Return approved operation callbacks for the dispatcher."""
        return {
            "get_machine_details": self.get_machine_details,
            "list_machines": self.list_machines,
            "get_work_orders": self.get_work_orders,
        }
