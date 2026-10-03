from enum import Enum
from pydantic import BaseModel, Field


class TargetSOVField(str, Enum):
    """The canonical 17 standard SOV fields in insurance property underwriting."""

    REFERENCE = "Reference"
    ADDRESS = "Address"
    CITY = "City"
    STATE = "State"
    ZIP = "Zip"
    COUNTY = "County"
    COUNTRY = "Country"
    BUILDING_VALUE = "Building Value"
    CONTENTS = "Contents"
    BI = "BI"
    OCCUPANCY = "Occupancy"
    CONSTRUCTION = "Construction"
    STOREYS = "Storeys"
    NUMBER_OF_BUILDINGS = "Number of Buildings"
    YEAR_BUILT = "Year Built"
    FIRE_SPRINKLERS = "Fire Sprinklers (Y/N)"
    OTHER = "Other"


TARGET_SOV_FIELDS: list[str] = [field.value for field in TargetSOVField]


class SchemaMapping(BaseModel):
    """Mapping from a source column in the raw sheet to a target SOV field."""

    source_column: str = Field(..., description="Original column header from the raw file")
    target_field: str = Field(
        ...,
        description="Target standard SOV field name (or 'Unmapped' if not mapped)",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    method: str = Field(
        ...,
        description="Mapping methodology (e.g. 'exact_match', 'fuzzy_match', 'llm_semantic', 'manual')",
    )
    reasoning: str = Field(
        ..., description="Explanation/justification for why this mapping was chosen"
    )


class SchemaMappingReport(BaseModel):
    """Aggregate schema mapping report for the selected sheet."""

    mappings: list[SchemaMapping] = Field(
        default_factory=list, description="List of column mappings"
    )
    unmapped_source_columns: list[str] = Field(
        default_factory=list, description="Source columns not mapped to any target field"
    )
    missing_target_fields: list[str] = Field(
        default_factory=list, description="Target standard fields without a mapped source column"
    )
