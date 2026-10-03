"""Pydantic models for table candidate evaluation and primary sheet selection."""

from pydantic import BaseModel, ConfigDict, Field


class TableCandidateSummary(BaseModel):
    """Evaluation summary for a single inspected table/sheet candidate."""

    model_config = ConfigDict(frozen=True)

    sheet_name: str = Field(
        ..., description="Name of the sheet or logical table"
    )
    is_candidate: bool = Field(
        ...,
        description="Whether this table qualifies as an SOV candidate table",
    )
    header_row: int | None = Field(
        default=None,
        ge=0,
        description="0-indexed header row detected in this table",
    )
    header_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence from HeaderDetector (0.0 to 1.0)",
    )
    semantic_concept_count: int = Field(
        default=0,
        ge=0,
        description="Count of distinct core SOV concepts identified in header",
    )
    data_density: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Post-header record data density (0.0 to 1.0)",
    )
    sheet_name_score: float = Field(
        default=0.0,
        description="Score adjustment based on positive sheet name signals",
    )
    negative_signal_penalty: float = Field(
        default=0.0,
        description="Penalty deducted for negative sheet name signals",
    )
    total_rows: int = Field(
        default=0,
        ge=0,
        description="Total raw rows present in this table",
    )
    usable_records: int = Field(
        default=0,
        ge=0,
        description="Count of data rows beneath the detected header",
    )
    final_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall composite table score (0.0 to 1.0)",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Step-by-step scoring factors for this sheet",
    )


class TableSelectionResult(BaseModel):
    """The result of evaluating all tables in a workbook and choosing the primary SOV table."""

    model_config = ConfigDict(frozen=True)

    selected_sheet: str | None = Field(
        default=None,
        description="Name of the chosen primary SOV table, or null if none qualifies",
    )
    selected_header_row: int | None = Field(
        default=None,
        ge=0,
        description="0-indexed header row for the selected sheet",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall selection confidence score (0.0 to 1.0)",
    )
    raw_headers: list[str] = Field(
        default_factory=list,
        description="Verbatim column header strings from the selected sheet",
    )
    detected_concepts: list[str] = Field(
        default_factory=list,
        description="Unique core concepts identified in the selected header",
    )
    is_near_tie: bool = Field(
        default=False,
        description="True if the top two candidates were within the near-tie threshold",
    )
    near_tie_candidates: list[str] = Field(
        default_factory=list,
        description="Names of candidate sheets involved in a near tie, if applicable",
    )
    candidates: list[TableCandidateSummary] = Field(
        default_factory=list,
        description="Complete audit list of all evaluated sheet candidates",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Explainable decision rationale for the winning table or disqualification",
    )
