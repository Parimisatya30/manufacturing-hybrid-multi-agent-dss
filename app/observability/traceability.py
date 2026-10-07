from dataclasses import dataclass, field
import re

from app.observability.logging import get_logger
from app.observability.metrics import metrics


logger = get_logger(__name__)


@dataclass
class TraceabilitySource:
    """Authoritative source used by the DSS."""

    source_id: str
    source_type: str
    title: str
    locator: str
    metadata: dict[str, str] = field(
        default_factory=dict
    )


@dataclass
class TraceabilityRecord:
    """Provenance information for a semantic or technical object."""

    identity_id: str
    object_type: str
    object_name: str
    source_ids: list[str] = field(
        default_factory=list
    )


class TraceabilityRegistry:
    """Central registry for DSS provenance and object identity."""

    def __init__(self) -> None:
        self._sources: dict[str, TraceabilitySource] = {}
        self._records: dict[str, TraceabilityRecord] = {}

    # ---------------------------------------------------------
    # Sources
    # ---------------------------------------------------------

    def register_source(
        self,
        source: TraceabilitySource,
    ) -> None:
        """Register an authoritative source."""

        self._sources[source.source_id] = source

        metrics.increment(
            "traceability_sources_registered_total"
        )

        logger.info(
            "Traceability source registered",
            extra={
                "source_id": source.source_id,
                "source_type": source.source_type,
            },
        )

    def get_source(
        self,
        source_id: str,
    ) -> TraceabilitySource | None:
        """Return a registered source."""

        return self._sources.get(source_id)

    def list_sources(
        self,
    ) -> list[TraceabilitySource]:
        """Return all registered sources."""

        return list(self._sources.values())

    # ---------------------------------------------------------
    # Identity / provenance
    # ---------------------------------------------------------

    def register(
        self,
        object_type: str,
        object_name: str,
        source_ids: list[str] | None = None,
    ) -> TraceabilityRecord:
        """Register an object and return its traceability record."""

        identity_id = self.build_identity_id(
            object_type,
            object_name,
        )

        record = TraceabilityRecord(
            identity_id=identity_id,
            object_type=object_type,
            object_name=object_name,
            source_ids=list(source_ids or []),
        )

        self._records[identity_id] = record

        metrics.increment(
            "traceability_records_registered_total"
        )

        logger.info(
            "Traceability record registered",
            extra={
                "identity_id": identity_id,
                "object_type": object_type,
                "object_name": object_name,
                "source_ids": record.source_ids,
            },
        )

        return record

    def get(
        self,
        identity_id: str,
    ) -> TraceabilityRecord | None:
        """Return a traceability record by identity."""

        return self._records.get(identity_id)

    def list_records(
        self,
    ) -> list[TraceabilityRecord]:
        """Return all traceability records."""

        return list(self._records.values())

    # ---------------------------------------------------------
    # Identity generation
    # ---------------------------------------------------------

    @staticmethod
    def build_identity_id(
        object_type: str,
        object_name: str,
    ) -> str:
        """Build a deterministic identity identifier."""

        normalized_type = (
            TraceabilityRegistry._normalize(object_type)
        )

        normalized_name = (
            TraceabilityRegistry._normalize(object_name)
        )

        return (
            f"{normalized_type}:{normalized_name}"
        )

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize an identity component."""

        value = value.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "-",
            value,
        )

        return value.strip("-")