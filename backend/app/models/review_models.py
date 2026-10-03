"""
review_models.py
----------------
Pydantic data models for the review layer.

Contains two groups of models:

Group 1 – Team models (preserved as-is):
    ReviewAction      — Enum for human review decisions (approve/reject/edit).
    ReviewDecision    — Row-level human reviewer decision used by orchestration/API.
    ReviewSubmission  — Batch payload of ReviewDecision entries.

Group 2 – Member 3 integration (added):
    DecisionType          — Enum for field-level decisions (ACCEPT/REJECT/EDIT).
    ReviewRecommendation  — AI-generated field-mapping recommendation (Agents 1-3 output).
    FieldReviewDecision   — Human reviewer's decision on a ReviewRecommendation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Group 1: Team models — preserved unchanged
# ---------------------------------------------------------------------------

class ReviewAction(str, Enum):
    """Supported human review decisions."""

    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class ReviewDecision(BaseModel):
    """Human reviewer decision for a specific recommendation or cell value."""

    row: int = Field(..., description="1-indexed row number")
    field: str = Field(..., description="Target field name")
    decision: str = Field(
        ...,
        description="Human decision: 'approve', 'reject', or 'edit'",
    )
    edited_value: Any | None = Field(
        default=None,
        description="User-supplied override value if decision is 'edit'",
    )
    reviewer: str = Field(
        default="human_reviewer",
        description="Identifier or email of the human reviewer who made the decision",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the decision was recorded",
    )


class ReviewSubmission(BaseModel):
    """Batch payload of human review decisions."""

    decisions: list[ReviewDecision] = Field(
        ..., description="List of decisions for the job recommendations"
    )
    notes: str | None = Field(default=None, description="Optional reviewer notes")


# ---------------------------------------------------------------------------
# Group 2: Member 3 integration — field-mapping review models
# ---------------------------------------------------------------------------

class DecisionType(str, Enum):
    """The three possible outcomes a human reviewer can choose for a field-level decision."""

    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    EDIT   = "EDIT"


class ReviewRecommendation(BaseModel):
    """
    Represents one AI-generated recommendation for a field mapping (Agents 1-3 output).

    - source_field    : The raw / original field name in the incoming SOV data.
    - target_field    : The standardised field name it should map to.
    - current_value   : The value currently sitting in source_field (can be anything).
    - recommendation  : The value the Agent recommends writing to target_field.
    - confidence      : How confident the Agent is (0.0 – 1.0).
    - reasoning       : A human-readable explanation of why this recommendation was made.
    """

    source_field:   str
    target_field:   str
    current_value:  Optional[Any] = None
    recommendation: Optional[Any] = None
    confidence:     float
    reasoning:      str

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_between_0_and_1(cls, value: float) -> float:
        """Confidence must be a probability: 0.0 ≤ confidence ≤ 1.0."""
        if not (0.0 <= value <= 1.0):
            raise ValueError(
                f"confidence must be between 0 and 1, got {value}"
            )
        return value


class FieldReviewDecision(BaseModel):
    """
    Records a human reviewer's decision on a single ReviewRecommendation.

    - source_field  : Must match the ReviewRecommendation's source_field.
    - target_field  : Must match the ReviewRecommendation's target_field.
    - decision      : ACCEPT, REJECT, or EDIT (DecisionType enum).
    - edited_value  : Required when decision is EDIT; must be provided.
    - approver      : Name / ID of the person making the decision (cannot be empty).
    """

    source_field:  str
    target_field:  str
    decision:      DecisionType
    edited_value:  Optional[Any] = None
    approver:      str

    @field_validator("approver")
    @classmethod
    def approver_cannot_be_empty(cls, value: str) -> str:
        """Approver name must not be blank."""
        if not value.strip():
            raise ValueError("approver cannot be an empty string")
        return value

    @model_validator(mode="after")
    def edited_value_required_when_edit(self) -> "FieldReviewDecision":
        """
        When the decision is EDIT, edited_value must be supplied.
        ACCEPT and REJECT do not require edited_value.
        """
        if self.decision == DecisionType.EDIT and self.edited_value is None:
            raise ValueError(
                "edited_value is required when decision is EDIT"
            )
        return self


# Member 3 standalone alias
Recommendation = ReviewRecommendation
