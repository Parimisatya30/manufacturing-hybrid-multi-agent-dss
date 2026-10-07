from app.observability.traceability import (
    TraceabilityRecord,
    TraceabilityRegistry,
    TraceabilitySource,
)


def test_register_source():
    registry = TraceabilityRegistry()

    source = TraceabilitySource(
        source_id="MES_SCHEMA",
        source_type="database",
        title="Manufacturing MES SQLite database",
        locator="data/raw/MES.db",
    )

    registry.register_source(source)

    result = registry.get_source("MES_SCHEMA")

    assert result is not None
    assert result.source_id == "MES_SCHEMA"
    assert result.source_type == "database"
    assert result.title == "Manufacturing MES SQLite database"
    assert result.locator == "data/raw/MES.db"


def test_list_sources():
    registry = TraceabilityRegistry()

    registry.register_source(
        TraceabilitySource(
            source_id="MES_SCHEMA",
            source_type="database",
            title="MES Database",
            locator="data/raw/MES.db",
        )
    )

    registry.register_source(
        TraceabilitySource(
            source_id="BUSINESS_SEMANTICS",
            source_type="json",
            title="Business Semantics",
            locator="data/semantic/business_semantics.json",
        )
    )

    sources = registry.list_sources()

    assert len(sources) == 2
    assert {source.source_id for source in sources} == {
        "MES_SCHEMA",
        "BUSINESS_SEMANTICS",
    }


def test_build_identity_id():
    identity_id = TraceabilityRegistry.build_identity_id(
        "entity",
        "Work Order",
    )

    assert identity_id == "entity:work-order"


def test_build_identity_id_normalizes_special_characters():
    identity_id = TraceabilityRegistry.build_identity_id(
        "attribute",
        "WorkOrder.Order ID",
    )

    assert identity_id == "attribute:workorder-order-id"


def test_register_entity_with_sources():
    registry = TraceabilityRegistry()

    record = registry.register(
        object_type="entity",
        object_name="WorkOrder",
        source_ids=["MES_SCHEMA", "BUSINESS_SEMANTICS"],
    )

    assert isinstance(record, TraceabilityRecord)
    assert record.identity_id == "entity:workorder"
    assert record.object_type == "entity"
    assert record.object_name == "WorkOrder"
    assert record.source_ids == [
        "MES_SCHEMA",
        "BUSINESS_SEMANTICS",
    ]

    result = registry.get("entity:workorder")

    assert result is not None
    assert result.identity_id == "entity:workorder"


def test_register_attribute():
    registry = TraceabilityRegistry()

    record = registry.register(
        object_type="attribute",
        object_name="WorkOrder.quantity",
        source_ids=["MES_SCHEMA"],
    )

    assert record.identity_id == "attribute:workorder-quantity"
    assert record.object_type == "attribute"
    assert record.object_name == "WorkOrder.quantity"
    assert record.source_ids == ["MES_SCHEMA"]


def test_register_metric():
    registry = TraceabilityRegistry()

    record = registry.register(
        object_type="metric",
        object_name="Production Quantity",
        source_ids=["MES_SCHEMA", "BUSINESS_SEMANTICS"],
    )

    assert record.identity_id == "metric:production-quantity"
    assert record.object_type == "metric"
    assert record.source_ids == [
        "MES_SCHEMA",
        "BUSINESS_SEMANTICS",
    ]


def test_list_records():
    registry = TraceabilityRegistry()

    registry.register(
        object_type="entity",
        object_name="WorkOrder",
        source_ids=["MES_SCHEMA"],
    )

    registry.register(
        object_type="attribute",
        object_name="WorkOrder.quantity",
        source_ids=["MES_SCHEMA"],
    )

    records = registry.list_records()

    assert len(records) == 2

    identity_ids = {
        record.identity_id
        for record in records
    }

    assert identity_ids == {
        "entity:workorder",
        "attribute:workorder-quantity",
    }


def test_register_without_sources():
    registry = TraceabilityRegistry()

    record = registry.register(
        object_type="entity",
        object_name="Machine",
    )

    assert record.identity_id == "entity:machine"
    assert record.source_ids == []


def test_register_replaces_existing_record():
    registry = TraceabilityRegistry()

    registry.register(
        object_type="entity",
        object_name="WorkOrder",
        source_ids=["MES_SCHEMA"],
    )

    registry.register(
        object_type="entity",
        object_name="WorkOrder",
        source_ids=[
            "MES_SCHEMA",
            "BUSINESS_SEMANTICS",
        ],
    )

    records = registry.list_records()

    assert len(records) == 1

    result = registry.get("entity:workorder")

    assert result is not None
    assert result.source_ids == [
        "MES_SCHEMA",
        "BUSINESS_SEMANTICS",
    ]