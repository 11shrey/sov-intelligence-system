from typing import Any
from pydantic import BaseModel, Field


class QualityIssue(BaseModel):
    """Represents a data quality defect, formatting anomaly, or missing value detected in the SOV dataset."""

    row: int = Field(..., description="1-indexed row number in the dataset")
    field: str = Field(..., description="Field/column name associated with the issue")
    issue: str = Field(..., description="Description of the quality issue or rule violation")
    severity: str = Field(
        ...,
        description="Severity level of the issue (e.g. 'info', 'warning', 'error', 'critical')",
    )
    current_value: Any = Field(..., description="Current raw value found in the cell")
    recommendation: str | None = Field(
        default=None,
        description="High-level description of proposed corrective action, if applicable",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in the issue detection (0.0 to 1.0)",
    )
    reasoning: str = Field(
        default="", description="Detailed rationale explaining why this was flagged"
    )


class Recommendation(BaseModel):
    """Actionable value-level fix proposed by Agent 3 for human review."""

    row: int = Field(..., description="1-indexed row number in the dataset")
    field: str = Field(..., description="Target field to receive the proposed value")
    action: str = Field(
        ...,
        description="Type of action (e.g. 'format_currency', 'fix_zip', 'impute_state', 'standardize_occupancy')",
    )
    current_value: Any = Field(..., description="Original raw value before transformation")
    proposed_value: Any = Field(..., description="Proposed cleaned / corrected value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the proposed recommendation (0.0 to 1.0)",
    )
    reasoning: str = Field(
        ..., description="Explanation and justification for the proposed correction"
    )


class QualityReport(BaseModel):
    """Aggregate quality inspection report."""

    total_rows_scanned: int = Field(default=0, description="Total rows scanned")
    issues: list[QualityIssue] = Field(
        default_factory=list, description="All detected quality issues"
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="All proposed recommendations"
    )
