"""Audit Service

Manages immutable event tracking for all system, agent, and human-in-the-loop actions.
"""

from datetime import datetime, timezone
from typing import Any
from app.models.audit_models import AuditEntry, AuditTrailReport
from app.orchestration.state import SOVProcessingState


class AuditService:
    """Service to create, append, and query audit trail logs."""

    def log_event(
        self,
        state: SOVProcessingState,
        user_id: str,
        action: str,
        source: str,
        target: str,
        before: Any,
        after: Any,
        confidence: float | None = None,
        approver: str | None = None,
    ) -> AuditEntry:
        """
        Record a new audit entry into the state audit log.

        Returns:
            AuditEntry: The created audit record.
        """
        entry = AuditEntry(
            job_id=state.job_id,
            user_id=user_id,
            action=action,
            source=source,
            target=target,
            before=before,
            after=after,
            confidence=confidence,
            approver=approver,
            timestamp=datetime.now(timezone.utc),
        )
        state.audit_log.append(entry)
        return entry

    def get_audit_trail(self, state: SOVProcessingState) -> AuditTrailReport:
        """
        Retrieve all audit entries for a job formatted as an AuditTrailReport.
        """
        return AuditTrailReport(
            job_id=state.job_id,
            total_entries=len(state.audit_log),
            entries=state.audit_log,
        )
