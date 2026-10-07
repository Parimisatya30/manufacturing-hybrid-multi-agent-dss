from app.observability.logging import get_logger
from app.observability.metrics import metrics

from app.semantic.models import (
    SemanticAttribute,
    SemanticEntity,
    SemanticMetric,
    SemanticRelationship,
)


logger = get_logger(__name__)


class SemanticCatalog:
    """Authoritative business semantic definitions for the DSS."""

    def __init__(self) -> None:
        self._entities: dict[str, SemanticEntity] = {}
        self._metrics: dict[str, SemanticMetric] = {}

    def add_entity(self, entity: SemanticEntity) -> None:
        """Add or replace a semantic entity."""

        key = entity.name.lower()

        self._entities[key] = entity

        metrics.increment("semantic_catalog_entities_total")

        logger.info(
            "Semantic entity registered",
            extra={
                "entity": entity.name,
                "table": entity.table_name,
            },
        )

    def get_entity(self, name: str) -> SemanticEntity | None:
        """Return an entity by name."""

        return self._entities.get(name.lower())

    def list_entities(self) -> list[SemanticEntity]:
        """Return all registered entities."""

        return list(self._entities.values())

    def add_attribute(
        self,
        entity_name: str,
        attribute: SemanticAttribute,
    ) -> None:
        """Add an attribute to an existing entity."""

        entity = self.get_entity(entity_name)

        if entity is None:
            raise ValueError(
                f"Semantic entity not found: {entity_name}"
            )

        entity.attributes.append(attribute)

        metrics.increment("semantic_catalog_attributes_total")

    def add_relationship(
        self,
        entity_name: str,
        relationship: SemanticRelationship,
    ) -> None:
        """Add a relationship to an existing entity."""

        entity = self.get_entity(entity_name)

        if entity is None:
            raise ValueError(
                f"Semantic entity not found: {entity_name}"
            )

        entity.relationships.append(relationship)

        metrics.increment("semantic_catalog_relationships_total")

    def add_metric(self, metric: SemanticMetric) -> None:
        """Register a business metric or KPI."""

        self._metrics[metric.name.lower()] = metric

        metrics.increment("semantic_catalog_metrics_total")

        logger.info(
            "Semantic metric registered",
            extra={
                "metric": metric.name,
                "source_table": metric.source_table,
            },
        )

    def get_metric(self, name: str) -> SemanticMetric | None:
        """Return a metric by name."""

        return self._metrics.get(name.lower())

    def list_metrics(self) -> list[SemanticMetric]:
        """Return all registered metrics."""

        return list(self._metrics.values())