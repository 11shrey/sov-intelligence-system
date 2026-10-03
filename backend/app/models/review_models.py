from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


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
