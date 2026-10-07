from dataclasses import dataclass

from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.tracing import tracer
from app.semantic.catalog import SemanticCatalog
from app.semantic.models import (
    SemanticAttribute,
    SemanticEntity,
)


logger = get_logger(__name__)


@dataclass
class EntityResolution:
    """Result of resolving a user term to a semantic entity."""

    query: str
    entity: SemanticEntity
    matched_by: str
    confidence: float


@dataclass
class AttributeResolution:
    """Result of resolving a user term to a semantic attribute."""

    query: str
    entity: SemanticEntity
    attribute: SemanticAttribute
    matched_by: str
    confidence: float


class SemanticResolver:
    """Resolve user terminology against the governed semantic catalog."""

    def __init__(
        self,
        catalog: SemanticCatalog,
    ) -> None:
        self.catalog = catalog

    def resolve_entity(
        self,
        query: str,
    ) -> EntityResolution | None:
        """Resolve a user term to a semantic entity."""

        with tracer.start_as_current_span(
            "semantic.resolve_entity"
        ) as span:

            span.set_attribute(
                "semantic.query",
                query,
            )

            normalized_query = self._normalize(
                query
            )

            metrics.increment(
                "semantic_entity_resolution_total"
            )

            # ---------------------------------------------------------
            # 1. Exact entity-name match
            # ---------------------------------------------------------

            for entity in self.catalog.list_entities():
                if (
                    self._normalize(entity.name)
                    == normalized_query
                ):
                    span.set_attribute(
                        "semantic.matched",
                        True,
                    )

                    span.set_attribute(
                        "semantic.matched_by",
                        "exact_name",
                    )

                    span.set_attribute(
                        "semantic.confidence",
                        1.0,
                    )

                    return self._entity_result(
                        query=query,
                        entity=entity,
                        matched_by="exact_name",
                        confidence=1.0,
                    )

            # ---------------------------------------------------------
            # 2. Entity synonym match
            # ---------------------------------------------------------

            for entity in self.catalog.list_entities():
                for synonym in entity.synonyms:
                    if (
                        self._normalize(synonym)
                        == normalized_query
                    ):
                        span.set_attribute(
                            "semantic.matched",
                            True,
                        )

                        span.set_attribute(
                            "semantic.matched_by",
                            "synonym",
                        )

                        span.set_attribute(
                            "semantic.confidence",
                            0.95,
                        )

                        return self._entity_result(
                            query=query,
                            entity=entity,
                            matched_by="synonym",
                            confidence=0.95,
                        )

            # ---------------------------------------------------------
            # No match
            # ---------------------------------------------------------

            span.set_attribute(
                "semantic.matched",
                False,
            )

            metrics.increment(
                "semantic_entity_resolution_not_found_total"
            )

            logger.info(
                "Semantic entity not found",
                extra={
                    "query": query,
                },
            )

            return None

    def resolve_attribute(
        self,
        entity_name: str,
        query: str,
    ) -> AttributeResolution | None:
        """Resolve a user term to an attribute of an entity."""

        with tracer.start_as_current_span(
            "semantic.resolve_attribute"
        ) as span:

            span.set_attribute(
                "semantic.entity",
                entity_name,
            )

            span.set_attribute(
                "semantic.query",
                query,
            )

            entity_resolution = (
                self.resolve_entity(
                    entity_name
                )
            )

            if entity_resolution is None:
                span.set_attribute(
                    "semantic.matched",
                    False,
                )

                logger.info(
                    "Cannot resolve attribute because entity was not found",
                    extra={
                        "entity": entity_name,
                        "attribute": query,
                    },
                )

                return None

            entity = entity_resolution.entity

            normalized_query = self._normalize(
                query
            )

            metrics.increment(
                "semantic_attribute_resolution_total"
            )

            # ---------------------------------------------------------
            # 1. Exact attribute-name match
            # ---------------------------------------------------------

            for attribute in entity.attributes:
                if (
                    self._normalize(attribute.name)
                    == normalized_query
                ):
                    span.set_attribute(
                        "semantic.matched",
                        True,
                    )

                    span.set_attribute(
                        "semantic.matched_by",
                        "exact_name",
                    )

                    span.set_attribute(
                        "semantic.confidence",
                        1.0,
                    )

                    return self._attribute_result(
                        query=query,
                        entity=entity,
                        attribute=attribute,
                        matched_by="exact_name",
                        confidence=1.0,
                    )

            # ---------------------------------------------------------
            # 2. Attribute synonym match
            # ---------------------------------------------------------

            for attribute in entity.attributes:
                for synonym in attribute.synonyms:
                    if (
                        self._normalize(synonym)
                        == normalized_query
                    ):
                        span.set_attribute(
                            "semantic.matched",
                            True,
                        )

                        span.set_attribute(
                            "semantic.matched_by",
                            "synonym",
                        )

                        span.set_attribute(
                            "semantic.confidence",
                            0.95,
                        )

                        return self._attribute_result(
                            query=query,
                            entity=entity,
                            attribute=attribute,
                            matched_by="synonym",
                            confidence=0.95,
                        )

            metrics.increment(
                "semantic_attribute_resolution_not_found_total"
            )

            span.set_attribute(
                "semantic.matched",
                False,
            )

            logger.info(
                "Semantic attribute not found",
                extra={
                    "entity": entity.name,
                    "query": query,
                },
            )

            return None

    def _entity_result(
        self,
        query: str,
        entity: SemanticEntity,
        matched_by: str,
        confidence: float,
    ) -> EntityResolution:
        """Create an entity resolution result."""

        metrics.increment(
            "semantic_entity_resolution_success_total"
        )

        logger.info(
            "Semantic entity resolved",
            extra={
                "query": query,
                "entity": entity.name,
                "matched_by": matched_by,
                "confidence": confidence,
            },
        )

        return EntityResolution(
            query=query,
            entity=entity,
            matched_by=matched_by,
            confidence=confidence,
        )

    def _attribute_result(
        self,
        query: str,
        entity: SemanticEntity,
        attribute: SemanticAttribute,
        matched_by: str,
        confidence: float,
    ) -> AttributeResolution:
        """Create an attribute resolution result."""

        metrics.increment(
            "semantic_attribute_resolution_success_total"
        )

        logger.info(
            "Semantic attribute resolved",
            extra={
                "query": query,
                "entity": entity.name,
                "attribute": attribute.name,
                "matched_by": matched_by,
                "confidence": confidence,
            },
        )

        return AttributeResolution(
            query=query,
            entity=entity,
            attribute=attribute,
            matched_by=matched_by,
            confidence=confidence,
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """Normalize terminology for deterministic matching."""

        return " ".join(
            value.strip()
            .lower()
            .replace("_", " ")
            .split()
        )