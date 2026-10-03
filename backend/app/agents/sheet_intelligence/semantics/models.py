"""Pydantic models for semantic concept detection."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class MatchedConcept(BaseModel):
    """Represents a single semantic concept detected within a cell string."""

    model_config = ConfigDict(frozen=True)

    concept: str = Field(
        ...,
        description="Canonical concept identifier (e.g. 'val_bldg', 'addr', 'location_signal')",
    )
    alias: str = Field(
        ...,
        description="The specific alias phrase that triggered the match (e.g. 'building cost')",
    )
    match_type: str = Field(
        default="phrase",
        description="Type of match: 'exact', 'phrase', or 'alias'",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence/signal strength of the concept detection",
    )


class CellDetection(BaseModel):
    """Detection results for a single raw cell in a row."""

    model_config = ConfigDict(frozen=True)

    raw_text: str | None = Field(
        default=None,
        description="Original verbatim cell text from the source sheet",
    )
    normalized_text: str = Field(
        default="",
        description="Normalized text used strictly for detection matching",
    )
    matched_concepts: list[MatchedConcept] = Field(
        default_factory=list,
        description="List of concepts matched on this cell",
    )
    is_ambiguous: bool = Field(
        default=False,
        description="True if cell matches an ambiguous signal rather than a definitive concept",
    )


class RowDetection(BaseModel):
    """Aggregate semantic analysis across all cells of a row."""

    model_config = ConfigDict(frozen=True)

    row_index: int | None = Field(
        default=None,
        description="0-indexed position of this row within the table/sheet",
    )
    raw_cells: list[Any] = Field(
        default_factory=list,
        description="Verbatim cell values in original column order",
    )
    cell_detections: list[CellDetection] = Field(
        default_factory=list,
        description="Per-cell detection outputs in column order",
    )
    distinct_concepts: list[str] = Field(
        default_factory=list,
        description="List of unique definitive SOV concept IDs detected in this row",
    )
    concept_count: int = Field(
        default=0,
        ge=0,
        description="Count of distinct definitive concepts found",
    )
    diversity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Diversity score (0.0 to 1.0) measuring conceptual breadth across columns",
    )
    ambiguous_signals: list[str] = Field(
        default_factory=list,
        description="List of ambiguous concept signals detected (e.g. 'location_signal')",
    )
