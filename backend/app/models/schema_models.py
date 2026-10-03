from enum import Enum
from typing import Optional
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
    """Mapping from a source column in the raw sheet to a target SOV field.

    target_field may be None when a source column could not be mapped to any
    of the 17 canonical fields (status will be 'rejected' or 'needs_review').
    """

    source_column: str = Field(..., description="Original column header from the raw file")
    target_field: Optional[str] = Field(
        default=None,
        description="Target standard SOV field name, or None if unmapped/rejected",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    method: str = Field(
        ...,
        description=(
            "Mapping methodology: 'exact', 'normalized', 'semantic_alias', "
            "'fuzzy', 'heuristic', 'llm', or 'unmapped'"
        ),
    )
    reasoning: str = Field(
        ..., description="Explanation/justification for why this mapping was chosen"
    )
    status: Optional[str] = Field(
        default=None,
        description=(
            "Mapping review status: 'approved', 'needs_review', or 'rejected'. "
            "None means the status has not been set."
        ),
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
