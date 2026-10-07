from app.database.schema import SchemaProfiler
from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.traceability import (
    TraceabilityRegistry,
)
from app.observability.tracing import tracer
from app.semantic.catalog import SemanticCatalog
from app.semantic.enricher import SemanticCatalogEnricher
from app.semantic.models import (
    SemanticAttribute,
    SemanticEntity,
    SemanticRelationship,
)
from app.semantic.repository import SemanticCatalogRepository


logger = get_logger(__name__)


class SemanticCatalogBuilder:
    """Build and synchronize the semantic catalog from the MES schema."""

    def __init__(
        self,
        profiler: SchemaProfiler,
        repository: SemanticCatalogRepository,
        enricher: SemanticCatalogEnricher,
        traceability: TraceabilityRegistry,
    ) -> None:
        self.profiler = profiler
        self.repository = repository
        self.enricher = enricher
        self.traceability = traceability

    def build(self) -> SemanticCatalog:
        """Synchronize technical metadata and apply business semantics."""

        with tracer.start_as_current_span(
            "semantic.catalog.build"
        ) as span:

            logger.info(
                "Starting semantic catalog build"
            )

            metrics.increment(
                "semantic_catalog_build_total"
            )

            schema = self.profiler.profile_database()

            span.set_attribute(
                "semantic.schema_table_count",
                len(schema),
            )

            existing_entities, existing_metrics = (
                self.repository.load()
            )

            existing_by_table = {
                entity.table_name: entity
                for entity in existing_entities
            }

            catalog = SemanticCatalog()

            # ---------------------------------------------------------
            # Step 1: Synchronize technical database metadata
            # ---------------------------------------------------------

            for table in schema:
                entity = existing_by_table.get(
                    table.name
                )

                if entity is None:
                    entity = self._create_entity(
                        table
                    )

                    logger.info(
                        "Created semantic entity",
                        extra={
                            "entity": entity.name,
                            "table": table.name,
                        },
                    )

                else:
                    self._synchronize_entity(
                        entity,
                        table,
                    )

                catalog.add_entity(entity)

            # Preserve existing business metrics.
            for metric in existing_metrics:
                catalog.add_metric(metric)

            # ---------------------------------------------------------
            # Step 2: Apply curated business semantics
            # ---------------------------------------------------------

            catalog = self.enricher.enrich(
                catalog
            )

            # ---------------------------------------------------------
            # Step 3: Register traceability
            # ---------------------------------------------------------

            with tracer.start_as_current_span(
                "semantic.traceability.register"
            ) as trace_span:

                self._register_traceability(
                    catalog
                )

                trace_span.set_attribute(
                    "traceability.record_count",
                    len(
                        self.traceability.list_records()
                    ),
                )

            # ---------------------------------------------------------
            # Step 4: Persist enriched catalog
            # ---------------------------------------------------------

            self.repository.save(
                catalog.list_entities(),
                catalog.list_metrics(),
            )

            metrics.increment(
                "semantic_catalog_build_success_total"
            )

            entity_count = len(
                catalog.list_entities()
            )

            metric_count = len(
                catalog.list_metrics()
            )

            traceability_count = len(
                self.traceability.list_records()
            )

            span.set_attribute(
                "semantic.entity_count",
                entity_count,
            )

            span.set_attribute(
                "semantic.metric_count",
                metric_count,
            )

            span.set_attribute(
                "semantic.traceability_count",
                traceability_count,
            )

            logger.info(
                "Semantic catalog build completed",
                extra={
                    "entity_count": entity_count,
                    "metric_count": metric_count,
                    "traceability_count": traceability_count,
                },
            )

            return catalog

    def _create_entity(
        self,
        table,
    ) -> SemanticEntity:
        """Create a semantic entity from a database table."""

        entity_name = self._to_entity_name(
            table.name
        )

        attributes = [
            SemanticAttribute(
                name=column.name,
                description="",
                table_name=table.name,
                column_name=column.name,
            )
            for column in table.columns
        ]

        relationships = [
            SemanticRelationship(
                source_entity=entity_name,
                relationship="references",
                target_entity=self._to_entity_name(
                    foreign_key.referenced_table
                ),
            )
            for foreign_key in table.foreign_keys
        ]

        return SemanticEntity(
            name=entity_name,
            description="",
            table_name=table.name,
            attributes=attributes,
            relationships=relationships,
        )

    def _synchronize_entity(
        self,
        entity: SemanticEntity,
        table,
    ) -> None:
        """Synchronize technical metadata while preserving business metadata."""

        existing_attributes = {
            attribute.column_name: attribute
            for attribute in entity.attributes
        }

        current_columns = {
            column.name: column
            for column in table.columns
        }

        # Add new database columns.
        for column_name in current_columns:
            if column_name not in existing_attributes:
                entity.attributes.append(
                    SemanticAttribute(
                        name=column_name,
                        description="",
                        table_name=table.name,
                        column_name=column_name,
                    )
                )

                logger.info(
                    "Added semantic attribute",
                    extra={
                        "table": table.name,
                        "column": column_name,
                    },
                )

        # Existing business metadata is intentionally preserved.
        # Removed database columns are not automatically deleted.

        existing_relationships = {
            (
                relationship.target_entity,
                relationship.relationship,
            )
            for relationship in entity.relationships
        }

        for foreign_key in table.foreign_keys:
            target_entity = self._to_entity_name(
                foreign_key.referenced_table
            )

            relationship_key = (
                target_entity,
                "references",
            )

            if relationship_key not in existing_relationships:
                entity.relationships.append(
                    SemanticRelationship(
                        source_entity=entity.name,
                        relationship="references",
                        target_entity=target_entity,
                    )
                )

    def _register_traceability(
        self,
        catalog: SemanticCatalog,
    ) -> None:
        """Register semantic objects with the central traceability registry."""

        for entity in catalog.list_entities():
            self.traceability.register(
                object_type="entity",
                object_name=entity.name,
                source_ids=entity.source_ids,
            )

            for attribute in entity.attributes:
                self.traceability.register(
                    object_type="attribute",
                    object_name=(
                        f"{entity.name}.{attribute.name}"
                    ),
                    source_ids=attribute.source_ids,
                )

        for metric in catalog.list_metrics():
            self.traceability.register(
                object_type="metric",
                object_name=metric.name,
                source_ids=metric.source_ids,
            )

        logger.info(
            "Semantic traceability registered",
            extra={
                "record_count": len(
                    self.traceability.list_records()
                ),
            },
        )

    @staticmethod
    def _to_entity_name(
        table_name: str,
    ) -> str:
        """Convert a database table name into a semantic entity name."""

        if table_name.endswith("ies"):
            return table_name[:-3] + "y"

        if table_name.endswith("s"):
            return table_name[:-1]

        return table_name


# -----------------------------------------------------------------
# Command-line entry point
# -----------------------------------------------------------------

if __name__ == "__main__":
    from app.config.settings import settings
    from app.database.sqlite import SQLiteClient
    from app.observability.traceability import (
        TraceabilitySource,
    )

    database = SQLiteClient(
        settings.MES_DATABASE_PATH
    )

    profiler = SchemaProfiler(database)

    repository = SemanticCatalogRepository(
        "data/semantic/catalog.json"
    )

    enricher = SemanticCatalogEnricher(
        "data/semantic/business_semantics.json"
    )

    traceability = TraceabilityRegistry()

    traceability.register_source(
        TraceabilitySource(
            source_id="MES_SCHEMA",
            source_type="database",
            title="Manufacturing MES SQLite database",
            locator="data/raw/MES.db",
        )
    )

    builder = SemanticCatalogBuilder(
        profiler,
        repository,
        enricher,
        traceability,
    )

    catalog = builder.build()

    print(
        f"Semantic catalog built: "
        f"{len(catalog.list_entities())} entities"
    )

    print(
        f"Traceability records: "
        f"{len(traceability.list_records())}"
    )