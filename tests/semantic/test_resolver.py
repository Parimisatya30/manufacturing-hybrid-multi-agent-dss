from app.semantic.catalog import SemanticCatalog
from app.semantic.models import SemanticAttribute, SemanticEntity
from app.semantic.resolver import SemanticResolver


def create_test_catalog() -> SemanticCatalog:
    """Create a small catalog for resolver unit tests."""

    catalog = SemanticCatalog()

    machine = SemanticEntity(
        name="Machine",
        description="Manufacturing machine",
        table_name="Machines",
        synonyms=[
            "equipment",
            "production machine",
        ],
    )

    machine.attributes.append(
        SemanticAttribute(
            name="MachineID",
            description="Unique machine identifier",
            table_name="Machines",
            column_name="MachineID",
            synonyms=[
                "machine id",
                "equipment id",
            ],
        )
    )

    catalog.add_entity(machine)

    return catalog


def test_resolve_entity_by_exact_name() -> None:
    catalog = create_test_catalog()
    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity("Machine")

    assert result is not None
    assert result.entity.name == "Machine"
    assert result.matched_by == "exact_name"
    assert result.confidence == 1.0


def test_resolve_entity_by_synonym() -> None:
    catalog = create_test_catalog()
    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity("equipment")

    assert result is not None
    assert result.entity.name == "Machine"
    assert result.matched_by == "synonym"
    assert result.confidence == 0.95


def test_resolve_attribute_by_exact_name() -> None:
    catalog = create_test_catalog()
    resolver = SemanticResolver(catalog)

    result = resolver.resolve_attribute(
        "Machine",
        "MachineID",
    )

    assert result is not None
    assert result.entity.name == "Machine"
    assert result.attribute.name == "MachineID"
    assert result.matched_by == "exact_name"
    assert result.confidence == 1.0


def test_resolve_attribute_by_synonym() -> None:
    catalog = create_test_catalog()
    resolver = SemanticResolver(catalog)

    result = resolver.resolve_attribute(
        "Machine",
        "equipment id",
    )

    assert result is not None
    assert result.entity.name == "Machine"
    assert result.attribute.name == "MachineID"
    assert result.matched_by == "synonym"
    assert result.confidence == 0.95


def test_resolve_unknown_entity() -> None:
    catalog = create_test_catalog()
    resolver = SemanticResolver(catalog)

    result = resolver.resolve_entity("UnknownThing")

    assert result is None