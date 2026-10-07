import json
from dataclasses import asdict
from pathlib import Path

from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.tracing import tracer
from app.semantic.models import (
    SemanticAttribute,
    SemanticEntity,
    SemanticMetric,
    SemanticRelationship,
)


logger = get_logger(__name__)


class SemanticCatalogRepository:
    """Persist and load the semantic catalog."""

    def __init__(
        self,
        catalog_path: str | Path,
    ) -> None:
        self.catalog_path = Path(
            catalog_path
        )

    def save(
        self,
        entities: list[SemanticEntity],
        metrics_definitions: list[SemanticMetric],
    ) -> None:
        """Save the semantic catalog to JSON."""

        with tracer.start_as_current_span(
            "semantic.repository.save"
        ) as span:

            self.catalog_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            payload = {
                "entities": [
                    asdict(entity)
                    for entity in entities
                ],
                "metrics": [
                    asdict(metric)
                    for metric in metrics_definitions
                ],
            }

            self.catalog_path.write_text(
                json.dumps(
                    payload,
                    indent=2,
                ),
                encoding="utf-8",
            )

            metrics.increment(
                "semantic_catalog_save_total"
            )

            span.set_attribute(
                "semantic.entity_count",
                len(entities),
            )

            span.set_attribute(
                "semantic.metric_count",
                len(metrics_definitions),
            )

            span.set_attribute(
                "semantic.catalog_path",
                str(self.catalog_path),
            )

            logger.info(
                "Semantic catalog saved",
                extra={
                    "catalog_path": str(
                        self.catalog_path
                    ),
                    "entity_count": len(
                        entities
                    ),
                    "metric_count": len(
                        metrics_definitions
                    ),
                },
            )

    def load(
        self,
    ) -> tuple[
        list[SemanticEntity],
        list[SemanticMetric],
    ]:
        """Load the semantic catalog from JSON."""

        with tracer.start_as_current_span(
            "semantic.repository.load"
        ) as span:

            if not self.catalog_path.exists():
                logger.info(
                    "Semantic catalog does not exist",
                    extra={
                        "catalog_path": str(
                            self.catalog_path
                        ),
                    },
                )

                span.set_attribute(
                    "semantic.catalog_exists",
                    False,
                )

                return [], []

            span.set_attribute(
                "semantic.catalog_exists",
                True,
            )

            payload = json.loads(
                self.catalog_path.read_text(
                    encoding="utf-8"
                )
            )

            entities = [
                self._entity_from_dict(item)
                for item in payload.get(
                    "entities",
                    [],
                )
            ]

            metrics_definitions = [
                SemanticMetric(**item)
                for item in payload.get(
                    "metrics",
                    [],
                )
            ]

            metrics.increment(
                "semantic_catalog_load_total"
            )

            span.set_attribute(
                "semantic.entity_count",
                len(entities),
            )

            span.set_attribute(
                "semantic.metric_count",
                len(metrics_definitions),
            )

            logger.info(
                "Semantic catalog loaded",
                extra={
                    "catalog_path": str(
                        self.catalog_path
                    ),
                    "entity_count": len(
                        entities
                    ),
                    "metric_count": len(
                        metrics_definitions
                    ),
                },
            )

            return (
                entities,
                metrics_definitions,
            )

    @staticmethod
    def _entity_from_dict(
        data: dict,
    ) -> SemanticEntity:
        """Reconstruct a SemanticEntity from JSON."""

        attributes = [
            SemanticAttribute(**attribute)
            for attribute in data.get(
                "attributes",
                [],
            )
        ]

        relationships = [
            SemanticRelationship(**relationship)
            for relationship in data.get(
                "relationships",
                [],
            )
        ]

        return SemanticEntity(
            name=data["name"],
            description=data["description"],
            table_name=data["table_name"],
            attributes=attributes,
            relationships=relationships,
            synonyms=data.get(
                "synonyms",
                [],
            ),
            source_ids=data.get(
                "source_ids",
                [],
            ),
        )