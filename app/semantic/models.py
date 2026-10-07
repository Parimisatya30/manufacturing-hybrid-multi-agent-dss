from dataclasses import dataclass, field


@dataclass
class SemanticAttribute:
    """Business meaning of a database attribute."""

    name: str
    description: str
    table_name: str
    column_name: str

    semantic_type: str = ""
    synonyms: list[str] = field(
        default_factory=list
    )
    unit: str = ""

    source_ids: list[str] = field(
        default_factory=list
    )


@dataclass
class SemanticRelationship:
    """Business relationship between two entities."""

    source_entity: str
    relationship: str
    target_entity: str


@dataclass
class SemanticEntity:
    """Business entity mapped to one or more database tables."""

    name: str
    description: str
    table_name: str

    attributes: list[SemanticAttribute] = field(
        default_factory=list
    )

    relationships: list[SemanticRelationship] = field(
        default_factory=list
    )

    # Business vocabulary
    synonyms: list[str] = field(
        default_factory=list
    )

    # Grounding / citation references
    source_ids: list[str] = field(
        default_factory=list
    )

@dataclass
class SemanticMetric:
    """Business metric or KPI."""

    name: str
    description: str

    # Database mapping
    source_table: str
    source_column: str | None = None

    # Business calculation
    formula: str | None = None

    # Metric unit
    unit: str = ""

    # Grounding / citation references
    source_ids: list[str] = field(
        default_factory=list
    )
    