"""Audit Service & Audit Logger

Manages immutable event tracking for all system, agent, and human-in-the-loop actions.
Integrates Member 3 AuditLogger and AuditRecord with team SOVProcessingState audit trail.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from app.models.audit_models import ApprovalStatus, AuditEntry, AuditRecord, AuditTrailReport
from app.models.review_models import DecisionType, Recommendation, ReviewDecision
from app.orchestration.state import SOVProcessingState


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_status_and_description(
    decision: ReviewDecision,
    before_value: Any,
    after_value: Any,
) -> tuple[ApprovalStatus, str]:
    """
    Derive the ApprovalStatus and transformation description from a decision.

    Rules
    -----
    ACCEPT → ACCEPTED
        Description says "Approved mapping" and notes if normalization occurred
        (i.e., before_value and after_value differ in type or representation).

    REJECT → REJECTED
        Description explains no transformation was applied.

    EDIT → EDITED
        Description says "Human edited value" and notes normalization if relevant.
    """
    raw_val = decision.decision.value if hasattr(decision.decision, "value") else str(decision.decision)
    dec_val = raw_val.lower()

    if dec_val in ("accept", "approved"):
        status = ApprovalStatus.ACCEPTED
        if _was_normalised(before_value, after_value):
            description = "Approved mapping + numeric standardization"
        else:
            description = "Approved mapping"

    elif dec_val in ("reject", "rejected"):
        status = ApprovalStatus.REJECTED
        description = "Recommendation rejected; no transformation applied"

    elif dec_val in ("edit", "edited"):
        status = ApprovalStatus.EDITED
        edited_val = getattr(decision, "edited_value", None)
        if _was_normalised(edited_val, after_value):
            description = "Human edited value + normalization applied"
        else:
            description = "Human edited value"

    else:
        raise ValueError(f"Unexpected decision type: {decision.decision}")

    return status, description


def _was_normalised(raw: Any, result: Any) -> bool:
    """
    Heuristic: did a normalization step change the value in a non-trivial way?

    We check whether the *type* changed (e.g. str → float) or whether the
    string representations differ noticeably (stripped "$", "," etc.).
    """
    if raw is None or result is None:
        return False
    if type(raw) != type(result):
        return True
    return str(raw).strip() != str(result).strip()


# ---------------------------------------------------------------------------
# AuditLogger — in-memory store + factory helpers (Member 3)
# ---------------------------------------------------------------------------

class AuditLogger:
    """
    In-memory audit log for the Member 3 SOV pipeline.

    Usage — manual record creation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        logger = AuditLogger()
        record = AuditRecord(...)
        logger.add(record)

    Usage — build from pipeline objects (recommended)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        logger = AuditLogger()
        logger.log_from_decision(
            recommendation=rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=1_250_000.0,
        )
    """

    def __init__(self) -> None:
        self._records: List[AuditRecord] = []

    # ------------------------------------------------------------------
    # Core store operations
    # ------------------------------------------------------------------

    def add(self, record: AuditRecord) -> None:
        """Append a pre-built AuditRecord to the log."""
        self._records.append(record)

    @property
    def records(self) -> List[AuditRecord]:
        """Return a copy of all stored AuditRecords (oldest first)."""
        return list(self._records)

    @property
    def count(self) -> int:
        """Total number of records stored."""
        return len(self._records)

    def clear(self) -> None:
        """Reset the logger — remove all records (useful between pipeline runs)."""
        self._records = []

    # ------------------------------------------------------------------
    # Factory helper — build a record from pipeline objects
    # ------------------------------------------------------------------

    def log_from_decision(
        self,
        recommendation: Recommendation,
        decision: ReviewDecision,
        before_value: Any,
        after_value: Any,
    ) -> AuditRecord:
        """
        Build and store one AuditRecord from a Recommendation + ReviewDecision.

        Parameters
        ----------
        recommendation : The AI recommendation that was reviewed.
        decision       : The human's ReviewDecision (ACCEPT / REJECT / EDIT).
        before_value   : Value in the source field before transformation.
        after_value    : Value in the target field after transformation.
                         For REJECT, pass the same as before_value.

        Returns
        -------
        The newly created AuditRecord (also stored internally).
        """
        status, description = _build_status_and_description(
            decision=decision,
            before_value=before_value,
            after_value=after_value,
        )

        source_field = getattr(recommendation, "source_field", None) or getattr(recommendation, "field", "unknown")
        target_field = getattr(recommendation, "target_field", None) or getattr(recommendation, "field", "unknown")
        confidence = getattr(recommendation, "confidence", 1.0)
        approver = getattr(decision, "approver", None) or getattr(decision, "reviewer", "reviewer")

        record = AuditRecord(
            source_field=source_field,
            target_field=target_field,
            before_value=before_value,
            after_value=after_value,
            transformation=description,
            confidence=confidence,
            approval_status=status,
            approver=approver,
        )
        self.add(record)
        return record

    # ------------------------------------------------------------------
    # Convenience queries
    # ------------------------------------------------------------------

    def records_by_status(self, status: ApprovalStatus) -> List[AuditRecord]:
        """Return all records that match a given ApprovalStatus."""
        return [r for r in self._records if r.approval_status == status]

    @property
    def accepted(self) -> List[AuditRecord]:
        """All ACCEPTED records."""
        return self.records_by_status(ApprovalStatus.ACCEPTED)

    @property
    def rejected(self) -> List[AuditRecord]:
        """All REJECTED records."""
        return self.records_by_status(ApprovalStatus.REJECTED)

    @property
    def edited(self) -> List[AuditRecord]:
        """All EDITED records."""
        return self.records_by_status(ApprovalStatus.EDITED)


# ---------------------------------------------------------------------------
# AuditService — team audit service extending AuditLogger
# ---------------------------------------------------------------------------

class AuditService(AuditLogger):
    """
    Service to create, append, and query audit trail logs.
    Supports both team SOVProcessingState event logging and Member 3 AuditLogger workflows.
    """

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

    def log_from_decision(
        self,
        recommendation: Recommendation,
        decision: ReviewDecision,
        before_value: Any,
        after_value: Any,
        state: Optional[SOVProcessingState] = None,
    ) -> AuditRecord:
        """
        Build and store an AuditRecord. If state is provided, also record an AuditEntry in state.audit_log.
        """
        record = super().log_from_decision(
            recommendation=recommendation,
            decision=decision,
            before_value=before_value,
            after_value=after_value,
        )

        if state is not None:
            self.log_event(
                state=state,
                user_id=decision.approver,
                action=f"transformation_{record.approval_status.value.lower()}",
                source=record.source_field,
                target=record.target_field,
                before=record.before_value,
                after=record.after_value,
                confidence=record.confidence,
                approver=record.approver,
            )

        return record
