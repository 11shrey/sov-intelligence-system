from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    """Immutable audit trail record documenting any system, agent, or human action."""

    job_id: str = Field(..., description="Unique job execution identifier")
    user_id: str = Field(..., description="System agent or user identity performing the action")
    action: str = Field(
        ...,
        description="Action performed (e.g. 'sheet_selected', 'schema_mapped', 'recommendation_approved', 'transformation_applied')",
    )
    source: str = Field(..., description="Source origin (e.g. raw column name, original cell)")
    target: str = Field(..., description="Target destination (e.g. standard field name, cleaned cell)")
    before: Any = Field(..., description="State or value before the action")
    after: Any = Field(..., description="State or value after the action")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score associated with the automated reasoning step",
    )
    approver: str | None = Field(
        default=None, description="Human approver ID who authorized this action, if applicable"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the audit entry was recorded",
    )


class AuditTrailReport(BaseModel):
    """Collection of audit entries for a complete job lifecycle."""

    job_id: str = Field(..., description="Associated job ID")
    total_entries: int = Field(default=0, description="Total audit events recorded")
    entries: list[AuditEntry] = Field(
        default_factory=list, description="Ordered audit trail entries"
    )
