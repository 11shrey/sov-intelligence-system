"""Pydantic contracts for Agent 1 -> Agent 2 handoff."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SemanticEvidenceItem(BaseModel):
    """Semantic evidence for a specific raw header column."""

    model_config = ConfigDict(frozen=True)

    column_index: int = Field(
        ..., ge=0, description="0-indexed column position in the selected sheet"
    )
    raw_text: str = Field(
        ..., description="Original raw text of the column header verbatim"
    )
    detected_concepts: list[str] = Field(
        default_factory=list,
        description="Identified core SOV concept IDs or directional signals",
    )
    matched_alias: str | None = Field(
        default=None,
        description="Specific alias that triggered the detection, if any",
    )
    is_ambiguous: bool = Field(
        default=False,
        description="Whether this cell triggered an ambiguous signal rather than a definitive concept",
    )


class SheetEvaluationAudit(BaseModel):
    """Compact audit summary of each evaluated table/sheet in the uploaded file."""

    model_config = ConfigDict(frozen=True)

    sheet_name: str = Field(..., description="Name of the sheet or table")
    is_candidate: bool = Field(
        ..., description="Whether this sheet qualified as an SOV candidate table"
    )
    header_row: int | None = Field(
        default=None,
        ge=0,
        description="0-indexed detected header row, or null if none detected",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Header detection confidence score (0.0 to 1.0)",
    )
    final_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall composite table score (0.0 to 1.0)",
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
    usable_records: int = Field(
        default=0,
        ge=0,
        description="Count of data rows beneath the detected header",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Evaluation rationale and scoring details",
    )


class Agent1HandoffResult(BaseModel):
    """Strict, machine-readable output contract passed from Agent 1 to Agent 2.

    Represents discovery results: selected sheet, header row, verbatim raw headers,
    representative raw sample rows, and audit reasoning.
    Does NOT contain canonical SOV schema mappings (Agent 2 responsibility).
    """

    model_config = ConfigDict(frozen=True)

    job_id: str = Field(..., description="Unique workflow execution identifier")
    source_file: str = Field(
        ..., description="Filename or path of the ingested source document"
    )
    file_type: str = Field(
        ..., description="Detected file extension/type ('xlsx', 'csv', 'json')"
    )
    selected_sheet: str | None = Field(
        default=None,
        description="Name of the primary SOV sheet/table, or null if no valid SOV table found",
    )
    header_row: int | None = Field(
        default=None,
        ge=0,
        description="0-indexed row containing table headers, or null if no valid header found",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall heuristic confidence in the sheet and header selection (0.0 to 1.0)",
    )
    raw_headers: list[str] = Field(
        default_factory=list,
        description="Verbatim, untransformed column header strings from the selected sheet",
    )
    sample_rows: list[list[Any]] = Field(
        default_factory=list,
        description="Up to 5 representative raw data rows beneath the header in original column order",
    )
    total_rows: int = Field(
        default=0,
        ge=0,
        description="Total count of data rows beneath the header in the selected table (excluding header)",
    )
    all_sheets_evaluated: list[SheetEvaluationAudit] = Field(
        default_factory=list,
        description="Audit trace of all sheets/tables evaluated in the file",
    )
    semantic_evidence: list[SemanticEvidenceItem] = Field(
        default_factory=list,
        description="Fine-grained semantic concept evidence per raw header column",
    )
    is_near_tie: bool = Field(
        default=False,
        description="True if top candidate sheets were in a near tie",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Deterministic, explainable rationale for sheet and header selection",
    )

    @field_validator("sample_rows", mode="before")
    @classmethod
    def sanitize_sample_rows(cls, v: Any) -> list[list[Any]]:
        """Ensure date, datetime, or Decimal objects in sample rows serialize cleanly to standard JSON types."""
        if not isinstance(v, list):
            return []

        sanitized_rows: list[list[Any]] = []
        for row in v:
            if not isinstance(row, (list, tuple)):
                continue
            sanitized_row: list[Any] = []
            for cell in row:
                if isinstance(cell, (datetime, date)):
                    sanitized_row.append(cell.isoformat())
                elif isinstance(cell, Decimal):
                    sanitized_row.append(float(cell))
                else:
                    sanitized_row.append(cell)
            sanitized_rows.append(sanitized_row)
        return sanitized_rows
