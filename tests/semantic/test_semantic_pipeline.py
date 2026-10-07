from app.config.settings import settings
from app.database.sqlite import SQLiteClient
from app.database.schema import SchemaProfiler
from app.observability.traceability import (
    TraceabilityRegistry,
    TraceabilitySource,
)
from app.semantic.builder import SemanticCatalogBuilder
from app.semantic.enricher import SemanticCatalogEnricher
from app.semantic.repository import SemanticCatalogRepository
from app.semantic.resolver import SemanticResolver


def build_real_catalog():
    """Build the semantic catalog using the real MES database."""

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
        profiler=profiler,
        repository=repository,
        enricher=enricher,
        traceability=traceability,
    )

    return builder.build()


def test_real_catalog_resolves_machine_synonym():
    catalog = build_real_catalog()

    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity(
        "equipment"
    )

    assert result is not None
    assert result.entity.name == "Machine"
    assert result.matched_by == "synonym"


def test_real_catalog_resolves_machine_attribute_synonym():
    catalog = build_real_catalog()

    resolver = SemanticResolver(catalog)

    result = resolver.resolve_attribute(
        "Machine",
        "equipment id",
    )

    assert result is not None
    assert result.entity.name == "Machine"
    assert result.attribute.name == "MachineID"
    assert result.matched_by == "synonym"


def test_real_catalog_resolves_work_order_synonym():
    catalog = build_real_catalog()

    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity(
        "production order"
    )

    assert result is not None
    assert result.entity.name == "WorkOrder"
    assert result.matched_by == "synonym"


def test_work_order_is_not_currently_resolved():
    catalog = build_real_catalog()

    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity(
        "work order"
    )

    assert result is None


def test_work_orders_is_not_currently_resolved():
    catalog = build_real_catalog()

    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity(
        "work orders"
    )

    assert result is None


def test_orders_of_work_is_not_currently_resolved():
    catalog = build_real_catalog()

    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity(
        "orders of work"
    )

    assert result is None