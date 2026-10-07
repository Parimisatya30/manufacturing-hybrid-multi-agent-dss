from app.semantic.catalog import SemanticCatalog
from app.semantic.models import (
    SemanticAttribute,
    SemanticEntity,
    SemanticMetric,
    SemanticRelationship,
)


def test_add_and_get_entity():
    catalog = SemanticCatalog()

    entity = SemanticEntity(
        name="Machine",
        description="Manufacturing equipment used for production.",
        table_name="Machines",
    )

    catalog.add_entity(entity)

    result = catalog.get_entity("machine")

    assert result is not None
    assert result.name == "Machine"
    assert result.table_name == "Machines"


def test_add_attribute():
    catalog = SemanticCatalog()

    catalog.add_entity(
        SemanticEntity(
            name="Machine",
            description="Manufacturing equipment.",
            table_name="Machines",
        )
    )

    attribute = SemanticAttribute(
        name="Machine Efficiency",
        description="Operational efficiency of the machine.",
        table_name="Machines",
        column_name="EfficiencyFactor",
    )

    catalog.add_attribute("Machine", attribute)

    entity = catalog.get_entity("Machine")

    assert entity is not None
    assert len(entity.attributes) == 1
    assert entity.attributes[0].column_name == "EfficiencyFactor"


def test_add_relationship():
    catalog = SemanticCatalog()

    catalog.add_entity(
        SemanticEntity(
            name="Machine",
            description="Manufacturing equipment.",
            table_name="Machines",
        )
    )

    relationship = SemanticRelationship(
        source_entity="Machine",
        relationship="belongs_to",
        target_entity="WorkCenter",
    )

    catalog.add_relationship("Machine", relationship)

    entity = catalog.get_entity("Machine")

    assert entity is not None
    assert entity.relationships[0].target_entity == "WorkCenter"


def test_add_metric():
    catalog = SemanticCatalog()

    metric = SemanticMetric(
        name="Machine Efficiency",
        description="Operational efficiency of a machine.",
        source_table="Machines",
        source_column="EfficiencyFactor",
    )

    catalog.add_metric(metric)

    result = catalog.get_metric("machine efficiency")

    assert result is not None
    assert result.source_table == "Machines"
    assert result.source_column == "EfficiencyFactor"