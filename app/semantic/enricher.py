import json
from pathlib import Path
from typing import Any

from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.tracing import tracer
from app.semantic.catalog import SemanticCatalog


logger = get_logger(__name__)


class SemanticCatalogEnricher:
    """Enrich a technical semantic catalog with business semantics."""

    def __init__(
        self,
        semantics_path: str | Path,
    ) -> None:
        self.semantics_path = Path(
            semantics_path
        )

    def enrich(
        self,
        catalog: SemanticCatalog,
    ) -> SemanticCatalog:
        """Apply business semantics to the technical catalog."""

        with tracer.start_as_current_span(
            "semantic.catalog.enrich"
        ) as span:

            logger.info(
                "Starting semantic catalog enrichment",
                extra={
                    "semantics_path": str(
                        self.semantics_path
                    ),
                },
            )

            span.set_attribute(
                "semantic.semantics_path",
                str(self.semantics_path),
            )

            metrics.increment(
                "semantic_catalog_enrichment_total"
            )

            with metrics.timer(
                "semantic_catalog_enrichment_duration_ms"
            ):
                semantics = self._load_semantics()

                self._enrich_entities(
                    catalog,
                    semantics,
                )

                self._enrich_attributes(
                    catalog,
                    semantics,
                )

                self._enrich_metrics(
                    catalog,
                    semantics,
                )

            metrics.increment(
                "semantic_catalog_enrichment_success_total"
            )

            entity_count = len(
                catalog.list_entities()
            )

            metric_count = len(
                catalog.list_metrics()
            )

            span.set_attribute(
                "semantic.entity_count",
                entity_count,
            )

            span.set_attribute(
                "semantic.metric_count",
                metric_count,
            )

            logger.info(
                "Semantic catalog enrichment completed",
                extra={
                    "entity_count": entity_count,
                    "metric_count": metric_count,
                },
            )

            return catalog

    def _load_semantics(
        self,
    ) -> dict[str, Any]:
        """Load curated business semantics from JSON."""

        if not self.semantics_path.exists():
            raise FileNotFoundError(
                f"Semantic definitions not found: "
                f"{self.semantics_path}"
            )

        with self.semantics_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _enrich_entities(
        self,
        catalog: SemanticCatalog,
        semantics: dict[str, Any],
    ) -> None:
        """Apply business meaning to semantic entities."""

        entity_definitions = semantics.get(
            "entities",
            {},
        )

        for entity in catalog.list_entities():
            definition = entity_definitions.get(
                entity.name
            )

            if definition is None:
                continue

            if definition.get("description"):
                entity.description = definition[
                    "description"
                ]

            entity.synonyms = self._merge_values(
                entity.synonyms,
                definition.get(
                    "synonyms",
                    [],
                ),
            )

            entity.source_ids = self._merge_values(
                entity.source_ids,
                definition.get(
                    "source_ids",
                    [],
                ),
            )

            logger.debug(
                "Enriched semantic entity",
                extra={
                    "entity": entity.name,
                },
            )

    def _enrich_attributes(
        self,
        catalog: SemanticCatalog,
        semantics: dict[str, Any],
    ) -> None:
        """Apply business meaning to semantic attributes."""

        attribute_definitions = semantics.get(
            "attributes",
            {},
        )

        for entity in catalog.list_entities():
            for attribute in entity.attributes:
                key = (
                    f"{entity.name}."
                    f"{attribute.name}"
                )

                definition = attribute_definitions.get(
                    key
                )

                if definition is None:
                    continue

                if definition.get("description"):
                    attribute.description = (
                        definition["description"]
                    )

                if definition.get("semantic_type"):
                    attribute.semantic_type = (
                        definition["semantic_type"]
                    )

                if definition.get("unit"):
                    attribute.unit = (
                        definition["unit"]
                    )

                attribute.synonyms = (
                    self._merge_values(
                        attribute.synonyms,
                        definition.get(
                            "synonyms",
                            [],
                        ),
                    )
                )

                attribute.source_ids = (
                    self._merge_values(
                        attribute.source_ids,
                        definition.get(
                            "source_ids",
                            [],
                        ),
                    )
                )

                logger.debug(
                    "Enriched semantic attribute",
                    extra={
                        "entity": entity.name,
                        "attribute": attribute.name,
                    },
                )

    def _enrich_metrics(
        self,
        catalog: SemanticCatalog,
        semantics: dict[str, Any],
    ) -> None:
        """Apply business meaning to semantic metrics."""

        metric_definitions = semantics.get(
            "metrics",
            {},
        )

        for metric in catalog.list_metrics():
            definition = metric_definitions.get(
                metric.name
            )

            if definition is None:
                continue

            if definition.get("description"):
                metric.description = (
                    definition["description"]
                )

            if definition.get("formula"):
                metric.formula = (
                    definition["formula"]
                )

            if definition.get("unit"):
                metric.unit = definition["unit"]

            metric.source_ids = (
                self._merge_values(
                    metric.source_ids,
                    definition.get(
                        "source_ids",
                        [],
                    ),
                )
            )

            logger.debug(
                "Enriched semantic metric",
                extra={
                    "metric": metric.name,
                },
            )

    @staticmethod
    def _merge_values(
        existing: list[str],
        new_values: list[str],
    ) -> list[str]:
        """Merge values while preserving order and uniqueness."""

        result = list(existing)

        for value in new_values:
            if value not in result:
                result.append(value)

        return result