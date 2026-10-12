
"""SQLite persistence for human approval decisions."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ApprovalRepository:
    """Persist approval decisions separately from the read-only MES database."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the approval table if it does not exist."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
                    approver TEXT,
                    reason TEXT NOT NULL,
                    decided_at TEXT,
                    created_at TEXT NOT NULL,
                    CHECK (
                        (status = 'PENDING' AND decided_at IS NULL)
                        OR
                        (status IN ('APPROVED', 'REJECTED')
                         AND approver IS NOT NULL
                         AND decided_at IS NOT NULL)
                    )
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_approval_request_id
                ON approval_decisions(request_id, id)
                """
            )

    def get_or_create_pending(
        self,
        request_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Return the latest existing record or create a pending record."""
        request_id = request_id.strip()

        if not request_id:
            raise ValueError("request_id is required.")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            row = connection.execute(
                """
                SELECT id, request_id, status, approver,
                       reason, decided_at, created_at
                FROM approval_decisions
                WHERE request_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (request_id,),
            ).fetchone()

            if row is not None:
                return dict(row)

            reason = reason.strip()
            if not reason:
                raise ValueError("Approval reason is required.")

            created_at = datetime.now(timezone.utc).isoformat()
            cursor = connection.execute(
                """
                INSERT INTO approval_decisions (
                    request_id, status, approver, reason,
                    decided_at, created_at
                )
                VALUES (?, 'PENDING', NULL, ?, NULL, ?)
                """,
                (request_id, reason, created_at),
            )

            row = connection.execute(
                """
                SELECT id, request_id, status, approver,
                       reason, decided_at, created_at
                FROM approval_decisions
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Failed to retrieve the approval record.")

        return dict(row)

    def create_pending(self, request_id: str, reason: str) -> dict[str, Any]:
        """Create a pending approval record for an investigation."""
        request_id = request_id.strip()
        reason = reason.strip()

        if not request_id:
            raise ValueError("request_id is required.")
        if not reason:
            raise ValueError("Approval reason is required.")

        created_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO approval_decisions (
                    request_id, status, approver, reason,
                    decided_at, created_at
                )
                VALUES (?, 'PENDING', NULL, ?, NULL, ?)
                """,
                (request_id, reason, created_at),
            )
            record_id = cursor.lastrowid

        record = self.get_by_id(record_id)
        if record is None:
            raise RuntimeError("Failed to retrieve the created approval record.")
        return record

    def get_by_id(self, record_id: int) -> dict[str, Any] | None:
        """Retrieve one approval record by its database ID."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, request_id, status, approver,
                       reason, decided_at, created_at
                FROM approval_decisions
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()

        return dict(row) if row else None

    def get_latest(self, request_id: str) -> dict[str, Any] | None:
        """Retrieve the latest approval record for an investigation."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, request_id, status, approver,
                       reason, decided_at, created_at
                FROM approval_decisions
                WHERE request_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (request_id,),
            ).fetchone()

        return dict(row) if row else None

    def decide(
        self,
        record_id: int,
        *,
        approver: str,
        approved: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Record one decision against a pending approval."""
        approver = approver.strip()
        reason = reason.strip()

        if not approver:
            raise ValueError("Approver identity is required.")
        if not reason:
            raise ValueError("Decision reason is required.")

        status = "APPROVED" if approved else "REJECTED"
        decided_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approval_decisions
                SET status = ?, approver = ?, reason = ?, decided_at = ?
                WHERE id = ? AND status = 'PENDING'
                """,
                (status, approver, reason, decided_at, record_id),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Approval record not found or no longer pending."
                )

            row = connection.execute(
                """
                SELECT id, request_id, status, approver,
                       reason, decided_at, created_at
                FROM approval_decisions
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()

        return dict(row)
