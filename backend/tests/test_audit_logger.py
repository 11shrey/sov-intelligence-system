"""
tests/test_audit_logger.py
--------------------------
Unit tests for the Audit Log module and AuditService.
Ported from Member 3 standalone test_audit_logger.py.
"""

from datetime import datetime, timezone
import copy
import pytest
from pydantic import ValidationError

from app.agents.transformation_agent import Agent4, Normalizer
from app.audit.audit_service import (
    ApprovalStatus,
    AuditLogger,
    AuditRecord,
    AuditService,
)
from app.models.review_models import DecisionType, Recommendation, ReviewDecision
from app.orchestration.state import SOVProcessingState
from app.review.human_review import HumanReview


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------

def make_rec(
    source: str = "Bldg Repl Cost",
    target: str = "Building Value",
    recommendation: object = "1250000",
    confidence: float = 0.95,
    current_value: object = "$1,250,000",
) -> Recommendation:
    return Recommendation(
        source_field=source,
        target_field=target,
        current_value=current_value,
        recommendation=recommendation,
        confidence=confidence,
        reasoning="Test recommendation.",
    )


def accept_decision(rec: Recommendation, approver: str = "Member 3") -> ReviewDecision:
    return HumanReview().accept(rec, approver=approver)


def reject_decision(rec: Recommendation, approver: str = "Member 3") -> ReviewDecision:
    return HumanReview().reject(rec, approver=approver)


def edit_decision(
    rec: Recommendation,
    edited_value: object,
    approver: str = "Member 3",
) -> ReviewDecision:
    return HumanReview().edit(rec, edited_value=edited_value, approver=approver)


@pytest.fixture
def logger() -> AuditLogger:
    return AuditLogger()


@pytest.fixture
def sample_rec() -> Recommendation:
    return make_rec()


# ===========================================================================
# 1. AuditRecord construction
# ===========================================================================

class TestAuditRecord:

    def test_create_valid_audit_record(self, sample_rec):
        """A fully specified AuditRecord should be created without error."""
        record = AuditRecord(
            source_field="Bldg Repl Cost",
            target_field="Building Value",
            before_value="$1,250,000",
            after_value=1_250_000.0,
            transformation="Approved mapping + numeric standardization",
            confidence=0.95,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Member 3",
        )
        assert record.source_field == "Bldg Repl Cost"
        assert record.target_field == "Building Value"
        assert record.before_value == "$1,250,000"
        assert record.after_value == 1_250_000.0
        assert record.approval_status == ApprovalStatus.ACCEPTED

    def test_record_preserves_confidence(self):
        """AuditRecord must store the AI confidence exactly."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.77,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Alice",
        )
        assert record.confidence == 0.77

    def test_record_preserves_approver(self):
        """AuditRecord must store the approver name exactly."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.5,
            approval_status=ApprovalStatus.REJECTED,
            approver="Bob",
        )
        assert record.approver == "Bob"

    def test_record_is_immutable(self):
        """AuditRecord must be frozen — mutation must raise an error."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.5,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Alice",
        )
        with pytest.raises(Exception):
            record.approver = "Hacker"  # type: ignore


# ===========================================================================
# 2. Timestamp
# ===========================================================================

class TestTimestamp:

    def test_timestamp_is_auto_generated(self):
        """Timestamp must be set automatically when the record is created."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.5,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Alice",
        )
        assert record.timestamp is not None
        assert isinstance(record.timestamp, datetime)

    def test_timestamp_is_timezone_aware(self):
        """Timestamp must be timezone-aware (UTC)."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.5,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Alice",
        )
        assert record.timestamp.tzinfo is not None

    def test_timestamp_is_utc(self):
        """Timestamp must be in UTC."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.5,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Alice",
        )
        assert record.timestamp.utcoffset().total_seconds() == 0

    def test_timestamps_are_distinct_for_separate_records(self):
        """Two records created must have datetime timestamps."""
        r1 = AuditRecord(
            source_field="F1", target_field="T1",
            before_value=None, after_value=None,
            transformation="t", confidence=0.1,
            approval_status=ApprovalStatus.ACCEPTED, approver="A",
        )
        r2 = AuditRecord(
            source_field="F2", target_field="T2",
            before_value=None, after_value=None,
            transformation="t", confidence=0.1,
            approval_status=ApprovalStatus.ACCEPTED, approver="A",
        )
        assert isinstance(r1.timestamp, datetime)
        assert isinstance(r2.timestamp, datetime)


# ===========================================================================
# 3. ACCEPT → ACCEPTED
# ===========================================================================

class TestAcceptAudit:

    def test_accept_produces_accepted_status(self, logger, sample_rec):
        """log_from_decision with ACCEPT must produce ApprovalStatus.ACCEPTED."""
        decision = accept_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=1_250_000.0,
        )
        assert record.approval_status == ApprovalStatus.ACCEPTED

    def test_accept_description_contains_approved(self, logger, sample_rec):
        """ACCEPT transformation description must mention 'Approved'."""
        decision = accept_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=1_250_000.0,
        )
        assert "approved" in record.transformation.lower()

    def test_accept_records_before_and_after_values(self, logger, sample_rec):
        """ACCEPT record must preserve both before and after values."""
        decision = accept_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=1_250_000.0,
        )
        assert record.before_value == "$1,250,000"
        assert record.after_value == 1_250_000.0


# ===========================================================================
# 4. REJECT → REJECTED
# ===========================================================================

class TestRejectAudit:

    def test_reject_produces_rejected_status(self, logger, sample_rec):
        """log_from_decision with REJECT must produce ApprovalStatus.REJECTED."""
        decision = reject_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value="$1,250,000",   # unchanged
        )
        assert record.approval_status == ApprovalStatus.REJECTED

    def test_reject_description_mentions_rejected(self, logger, sample_rec):
        """REJECT transformation description must mention 'rejected'."""
        decision = reject_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value="$1,250,000",
        )
        assert "rejected" in record.transformation.lower()

    def test_reject_before_and_after_values_match(self, logger, sample_rec):
        """
        A REJECT record's before_value and after_value should be the same,
        showing the data was NOT changed.
        """
        decision = reject_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value="$1,250,000",
        )
        assert record.before_value == record.after_value

    def test_reject_is_not_accepted(self, logger, sample_rec):
        """A REJECTED record must NEVER have approval_status ACCEPTED."""
        decision = reject_decision(sample_rec)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value="$1,250,000",
        )
        assert record.approval_status != ApprovalStatus.ACCEPTED


# ===========================================================================
# 5. EDIT → EDITED
# ===========================================================================

class TestEditAudit:

    def test_edit_produces_edited_status(self, logger, sample_rec):
        """log_from_decision with EDIT must produce ApprovalStatus.EDITED."""
        decision = edit_decision(sample_rec, edited_value=2_000_000)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=2_000_000.0,
        )
        assert record.approval_status == ApprovalStatus.EDITED

    def test_edit_description_mentions_human(self, logger, sample_rec):
        """EDIT transformation description must mention 'Human'."""
        decision = edit_decision(sample_rec, edited_value=2_000_000)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=2_000_000.0,
        )
        assert "human" in record.transformation.lower()

    def test_edit_records_correct_after_value(self, logger, sample_rec):
        """EDIT record's after_value must be the human-edited value."""
        decision = edit_decision(sample_rec, edited_value=9_999_000)
        record = logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=9_999_000,
        )
        assert record.after_value == 9_999_000


# ===========================================================================
# 6. AuditLogger store operations
# ===========================================================================

class TestAuditLoggerStore:

    def test_logger_starts_empty(self, logger):
        """A new AuditLogger must have zero records."""
        assert logger.count == 0
        assert logger.records == []

    def test_add_record_increments_count(self, logger):
        """Adding one record must make count == 1."""
        record = AuditRecord(
            source_field="F", target_field="T",
            before_value=None, after_value=None,
            transformation="test",
            confidence=0.5,
            approval_status=ApprovalStatus.ACCEPTED,
            approver="Alice",
        )
        logger.add(record)
        assert logger.count == 1

    def test_records_returns_all_stored_records(self, logger, sample_rec):
        """records property must return every stored AuditRecord."""
        d1 = accept_decision(sample_rec)
        d2 = reject_decision(sample_rec)

        rec1 = logger.log_from_decision(sample_rec, d1, "$1,250,000", 1_250_000.0)
        rec2 = logger.log_from_decision(sample_rec, d2, "$1,250,000", "$1,250,000")

        all_records = logger.records
        assert len(all_records) == 2
        assert rec1 in all_records
        assert rec2 in all_records

    def test_clear_resets_logger(self, logger, sample_rec):
        """clear() must remove all records and reset count to 0."""
        decision = accept_decision(sample_rec)
        logger.log_from_decision(sample_rec, decision, "$1,250,000", 1_250_000.0)
        assert logger.count == 1

        logger.clear()

        assert logger.count == 0
        assert logger.records == []

    def test_multiple_records_stored(self, logger):
        """AuditLogger must be able to store many records."""
        for i in range(10):
            record = AuditRecord(
                source_field=f"Field_{i}",
                target_field=f"Target_{i}",
                before_value=None,
                after_value=None,
                transformation="batch test",
                confidence=0.5,
                approval_status=ApprovalStatus.ACCEPTED,
                approver="Alice",
            )
            logger.add(record)
        assert logger.count == 10

    def test_records_returns_copy_not_internal_list(self, logger, sample_rec):
        """Mutating the returned list must not corrupt the logger's internal state."""
        decision = accept_decision(sample_rec)
        logger.log_from_decision(sample_rec, decision, "$1,250,000", 1_250_000.0)

        returned = logger.records
        returned.clear()

        assert logger.count == 1


# ===========================================================================
# 7. Convenience queries
# ===========================================================================

class TestLoggerQueries:

    def _add_mixed(self, logger: AuditLogger) -> None:
        """Add one ACCEPTED, one REJECTED, one EDITED record."""
        rec_a = make_rec(source="FA", target="TA")
        rec_r = make_rec(source="FR", target="TR")
        rec_e = make_rec(source="FE", target="TE")

        logger.log_from_decision(rec_a, accept_decision(rec_a), "before", "after")
        logger.log_from_decision(rec_r, reject_decision(rec_r), "before", "before")
        logger.log_from_decision(rec_e, edit_decision(rec_e, "edited"), "before", "edited")

    def test_accepted_property(self, logger):
        """logger.accepted must return only ACCEPTED records."""
        self._add_mixed(logger)
        assert len(logger.accepted) == 1
        assert all(r.approval_status == ApprovalStatus.ACCEPTED for r in logger.accepted)

    def test_rejected_property(self, logger):
        """logger.rejected must return only REJECTED records."""
        self._add_mixed(logger)
        assert len(logger.rejected) == 1
        assert all(r.approval_status == ApprovalStatus.REJECTED for r in logger.rejected)

    def test_edited_property(self, logger):
        """logger.edited must return only EDITED records."""
        self._add_mixed(logger)
        assert len(logger.edited) == 1
        assert all(r.approval_status == ApprovalStatus.EDITED for r in logger.edited)


# ===========================================================================
# 8. Pending recommendations must NOT produce ACCEPTED audit records
# ===========================================================================

class TestPendingNotAccepted:

    def test_pending_recommendation_is_not_logged_as_accepted(self, logger, sample_rec):
        """
        A pending recommendation (no decision) must never be logged
        as an ACCEPTED audit record.
        """
        assert logger.count == 0
        assert len(logger.accepted) == 0

    def test_logging_only_decided_items(self, logger):
        """
        When we selectively log only ACCEPT and REJECT (not the pending one),
        the logger must contain exactly 2 records, none of which is for the pending field.
        """
        rec_accept = make_rec(source="FA", target="TA", recommendation="v1")
        rec_reject = make_rec(source="FR", target="TR", recommendation="v2")
        rec_pending = make_rec(source="FP", target="TP", recommendation="v3")

        logger.log_from_decision(rec_accept, accept_decision(rec_accept), "v1_raw", "v1_clean")
        logger.log_from_decision(rec_reject, reject_decision(rec_reject), "v2_raw", "v2_raw")

        assert logger.count == 2
        target_fields_logged = {r.target_field for r in logger.records}
        assert "TP" not in target_fields_logged


# ===========================================================================
# 9. Source data safety
# ===========================================================================

class TestSourceDataSafety:

    def test_audit_logging_does_not_modify_source_row(self, logger, sample_rec):
        """
        Running log_from_decision must not mutate the source data dict
        or the original Recommendation object.
        """
        source_row = {"Bldg Repl Cost": "$1,250,000", "Other": "unchanged"}
        source_snapshot = copy.deepcopy(source_row)

        rec_snapshot_confidence = sample_rec.confidence
        decision = accept_decision(sample_rec)

        logger.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value=source_row["Bldg Repl Cost"],
            after_value=1_250_000.0,
        )

        assert source_row == source_snapshot
        assert sample_rec.confidence == rec_snapshot_confidence


# ===========================================================================
# 10. End-to-end: full pipeline → audit log
# ===========================================================================

class TestEndToEndPipeline:

    def test_full_pipeline_produces_correct_audit_records(self, logger):
        """
        Run a mini end-to-end:
            source_row → Agent4.transform() → AuditLogger.log_from_decision()
        Verify the audit trail is complete and correct.
        """
        source_row = {
            "Bldg Repl Cost":  "$1,250,000",
            "Fire Prot.":      "YES",
            "Rejected Field":  "some_value",
        }

        rec1 = make_rec("Bldg Repl Cost", "Building Value",         recommendation="1250000")
        rec2 = make_rec("Fire Prot.",     "Fire Sprinklers (Y/N)",   recommendation="YES", current_value="YES")
        rec3 = make_rec("Rejected Field", "Rejected Target",         recommendation="rvalue")

        hr = HumanReview()
        d1 = hr.accept(rec1, approver="Member 3")
        d2 = hr.edit(rec2, edited_value="N", approver="Member 3")
        d3 = hr.reject(rec3, approver="Member 3")

        agent = Agent4()
        result = agent.transform(source_row, [rec1, rec2, rec3], [d1, d2, d3])

        logger.log_from_decision(rec1, d1,
            before_value=source_row["Bldg Repl Cost"],
            after_value=result.transformed_data.get("Building Value"))

        logger.log_from_decision(rec2, d2,
            before_value=source_row["Fire Prot."],
            after_value=result.transformed_data.get("Fire Sprinklers (Y/N)"))

        logger.log_from_decision(rec3, d3,
            before_value=source_row["Rejected Field"],
            after_value=source_row["Rejected Field"])

        assert logger.count == 3
        assert len(logger.accepted) == 1
        assert len(logger.edited) == 1
        assert len(logger.rejected) == 1

        acc = logger.accepted[0]
        assert acc.source_field == "Bldg Repl Cost"
        assert acc.before_value == "$1,250,000"
        assert acc.after_value  == 1_250_000.0
        assert acc.approver     == "Member 3"

        edt = logger.edited[0]
        assert edt.source_field == "Fire Prot."
        assert edt.after_value  == "N"

        rej = logger.rejected[0]
        assert rej.source_field  == "Rejected Field"
        assert rej.before_value  == rej.after_value
        assert "rejected" in rej.transformation.lower()

        assert source_row["Bldg Repl Cost"] == "$1,250,000"


# ===========================================================================
# 11. Team AuditService integration tests
# ===========================================================================

class TestTeamAuditService:

    def test_audit_service_log_event(self):
        from app.orchestration.state import FileInfo
        file_info = FileInfo(filename="sov.xlsx", file_path="data/sov.xlsx", file_size_bytes=100)
        state = SOVProcessingState(job_id="job-test-audit", file_info=file_info)
        service = AuditService()
        entry = service.log_event(
            state=state,
            user_id="user_123",
            action="recommendation_approved",
            source="Bldg Cost",
            target="Building Value",
            before="$1,000",
            after=1000.0,
            confidence=0.9,
            approver="Risk Officer",
        )
        assert entry.job_id == "job-test-audit"
        assert len(state.audit_log) == 1
        report = service.get_audit_trail(state)
        assert report.total_entries == 1
        assert report.entries[0] == entry

    def test_audit_service_log_from_decision_with_state(self, sample_rec):
        from app.orchestration.state import FileInfo
        file_info = FileInfo(filename="sov.xlsx", file_path="data/sov.xlsx", file_size_bytes=100)
        state = SOVProcessingState(job_id="job-test-combined", file_info=file_info)
        service = AuditService()
        decision = accept_decision(sample_rec, approver="Lead Underwriter")

        record = service.log_from_decision(
            recommendation=sample_rec,
            decision=decision,
            before_value="$1,250,000",
            after_value=1250000.0,
            state=state,
        )

        assert record.approval_status == ApprovalStatus.ACCEPTED
        assert service.count == 1
        assert len(state.audit_log) == 1
        assert state.audit_log[0].target == "Building Value"
        assert state.audit_log[0].approver == "Lead Underwriter"
