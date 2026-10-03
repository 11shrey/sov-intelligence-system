from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Severity and Issue-Type enumerations
# (used internally by Agent 3; serialised as string values in the API)
# ---------------------------------------------------------------------------

class IssueSeverity(str, Enum):
    """Severity level of a detected data quality issue."""

    low = "low"
    medium = "medium"
    high = "high"

    # Legacy string aliases accepted by the shared contract
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class IssueType(str, Enum):
    """Broad category of a quality issue detected by Agent 3."""

    missing_value = "missing_value"
    invalid_numeric = "invalid_numeric"
    invalid_year = "invalid_year"
    invalid_sprinkler = "invalid_sprinkler"
    duplicate_record = "duplicate_record"
    inconsistent_value = "inconsistent_value"
    suspicious_value = "suspicious_value"
    invalid_value = "invalid_value"


# ---------------------------------------------------------------------------
# Shared contracts
# ---------------------------------------------------------------------------

class QualityIssue(BaseModel):
    """Represents a data quality defect, formatting anomaly, or missing value
    detected in the SOV dataset.

    The shared contract fields (``current_value``, ``issue``, ``severity``,
    ``confidence``, ``recommendation``, ``reasoning``) are preserved.

    Agent 3 also populates ``issue_type`` and ``value`` (alias of
    ``current_value``) for richer internal processing.
    """

    row: int = Field(..., description="1-indexed row number in the dataset")
    field: str = Field(..., description="Field/column name associated with the issue")
    issue: str = Field(..., description="Description of the quality issue or rule violation")
    severity: str = Field(
        ...,
        description="Severity level of the issue (e.g. 'low', 'medium', 'high')",
    )
    current_value: Any = Field(..., description="Current raw value found in the cell")
    recommendation: Optional[str] = Field(
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
    # Extended field used by Agent 3 (mirrors current_value; kept separate to
    # avoid aliasing complexity while staying backward-compatible)
    value: Any = Field(
        default=None,
        description="Alias of current_value populated by Agent 3 internal checks",
    )
    issue_type: Optional[str] = Field(
        default=None,
        description=(
            "Structured issue category (e.g. 'missing_value', 'invalid_numeric'). "
            "Populated by Agent 3."
        ),
    )
    requires_human_review: bool = Field(
        default=False,
        description="Whether this issue requires human review under the routing policy",
    )
    reasoning_source: str = Field(
        default="deterministic",
        description="Source of reasoning: 'deterministic', 'qwen', or 'qwen_fallback'",
    )
    qwen_used: bool = Field(
        default=False,
        description="Whether contextual reasoning with Qwen was invoked for this issue",
    )
    proposed_value: Any = Field(
        default=None,
        description="Proposed replacement value (always None for Agent 3 advisory reasoning)",
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
    proposed_value: Optional[Any] = Field(
        default=None,
        description="Proposed cleaned / corrected value (None for advisory issues)",
    )
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
    total_issues: int = Field(default=0, description="Total number of issues detected")
    issues: list[QualityIssue] = Field(
        default_factory=list, description="All detected quality issues"
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="All proposed recommendations"
    )
    summary: dict[str, int] = Field(
        default_factory=dict,
        description="Issue-type → count breakdown",
    )
