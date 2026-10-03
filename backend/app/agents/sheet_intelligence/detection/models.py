"""Pydantic models for header row detection and candidate evaluation."""

from pydantic import BaseModel, ConfigDict, Field


class CandidateRowDetail(BaseModel):
    """Detailed audit information for an evaluated candidate header row."""

    model_config = ConfigDict(frozen=True)

    row_index: int = Field(
        ..., ge=0, description="0-indexed position of this row in the table"
    )
    distinct_concepts: list[str] = Field(
        default_factory=list,
        description="Core SOV concepts identified in this row",
    )
    concept_count: int = Field(
        ..., ge=0, description="Count of distinct core SOV concepts"
    )
    populated_cells: int = Field(
        ..., ge=0, description="Number of non-empty cells in this row"
    )
    data_density_below: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Populated cell density of the rows directly beneath this candidate",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Deterministic composite score for this candidate row",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Step-by-step scoring factors for this candidate",
    )


class HeaderDetectionResult(BaseModel):
    """Result of header row detection on a single table/sheet."""

    model_config = ConfigDict(frozen=True)

    header_row: int | None = Field(
        default=None,
        ge=0,
        description="0-indexed header row index, or null if no valid header detected",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in the detected header row (0.0 to 1.0)",
    )
    raw_headers: list[str] = Field(
        default_factory=list,
        description="Verbatim source header text in original column order",
    )
    detected_concepts: list[str] = Field(
        default_factory=list,
        description="List of distinct core concepts identified in the chosen header row",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Explainable breakdown of why this row was selected or rejected",
    )
    candidate_rows: list[CandidateRowDetail] = Field(
        default_factory=list,
        description="Audit trace of all inspected candidate rows and their scores",
    )
