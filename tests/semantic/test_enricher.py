import json

from app.semantic.catalog import SemanticCatalog
from app.semantic.enricher import SemanticCatalogEnricher
from app.semantic.models import (
    SemanticAttribute,
    SemanticEntity,
)


def create_catalog() -> SemanticCatalog:
    catalog = SemanticCatalog()

    machine = SemanticEntity(
        name="Machine",
        description="",
        table_name="Machines",
        attributes=[
            SemanticAttribute(
                name="MachineID",
                description="",
                table_name="Machines",
                column_name="MachineID",
            ),
            SemanticAttribute(
                name="Status",
                description="",
                table_name="Machines",
                column_name="Status",
            ),
            SemanticAttribute(
                name="EfficiencyFactor",
                description="",
                table_name="Machines",
                column_name="EfficiencyFactor",
            ),
        ],
    )

    catalog.add_entity(machine)

    return catalog


def create_semantics_file(tmp_path):
    semantics = {
        "sources": [
            {
                "source_id": "MES_SCHEMA",
                "source_type": "database",
                "title": "Manufacturing MES SQLite database",
                "locator": "data/raw/MES.db",
            }
        ],
        "entities": {
            "Machine": {
                "description": (
                    "Manufacturing machine or "
                    "production equipment."
                ),
                "synonyms": [
                    "equipment",
                    "production machine",
                ],
                "source_ids": [
                    "MES_SCHEMA",
                ],
            }
        },
        "attributes": {
            "Machine.MachineID": {
                "description": (
                    "Unique identifier for a machine."
                ),
                "semantic_type": "identifier",
                "synonyms": [
                    "machine id",
                    "equipment id",
                ],
                "source_ids": [
                    "MES_SCHEMA",
                ],
            },
            "Machine.Status": {
                "description": (
                    "Current operating status "
                    "of the machine."
                ),
                "semantic_type": "status",
                "synonyms": [
                    "machine state",
                    "equipment status",
                ],
                "source_ids": [
                    "MES_SCHEMA",
                ],
            },
        },
        "metrics": {},
    }

    path = tmp_path / "business_semantics.json"

    path.write_text(
        json.dumps(semantics, indent=2),
        encoding="utf-8",
    )

    return path


def test_enrich_entity(tmp_path):
    catalog = create_catalog()

    semantics_path = create_semantics_file(
        tmp_path
    )

    enricher = SemanticCatalogEnricher(
        semantics_path
    )

    enriched = enricher.enrich(catalog)

    machine = enriched.list_entities()[0]

    assert machine.description == (
        "Manufacturing machine or "
        "production equipment."
    )

    assert "equipment" in machine.synonyms

    assert "MES_SCHEMA" in machine.source_ids


def test_enrich_attribute(tmp_path):
    catalog = create_catalog()

    semantics_path = create_semantics_file(
        tmp_path
    )

    enricher = SemanticCatalogEnricher(
        semantics_path
    )

    enriched = enricher.enrich(catalog)

    machine = enriched.list_entities()[0]

    machine_id = next(
        attribute
        for attribute in machine.attributes
        if attribute.name == "MachineID"
    )

    assert machine_id.semantic_type == "identifier"

    assert "machine id" in machine_id.synonyms

    assert "MES_SCHEMA" in machine_id.source_ids


def test_unmapped_attribute_is_preserved(tmp_path):
    catalog = create_catalog()

    semantics_path = create_semantics_file(
        tmp_path
    )

    enricher = SemanticCatalogEnricher(
        semantics_path
    )

    enriched = enricher.enrich(catalog)

    machine = enriched.list_entities()[0]

    efficiency = next(
        attribute
        for attribute in machine.attributes
        if attribute.name == "EfficiencyFactor"
    )

    # Technical metadata must remain untouched.
    assert efficiency.table_name == "Machines"
    assert efficiency.column_name == (
        "EfficiencyFactor"
    )

    # No business definition exists yet.
    assert efficiency.description == ""
