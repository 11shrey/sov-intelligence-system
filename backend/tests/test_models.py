"""Test Pydantic models and data contracts."""

from datetime import datetime
from app.models.sheet_models import SheetAnalysis
from app.models.schema_models import SchemaMapping, TARGET_SOV_FIELDS, TargetSOVField
from app.models.quality_models import QualityIssue, Recommendation
from app.models.review_models import ReviewDecision, ReviewSubmission
from app.models.transformation_models import Transformation
from app.models.audit_models import AuditEntry
from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus


def test_target_sov_fields_count():
    """Verify standard SOV schema defines exactly 17 canonical fields."""
    assert len(TARGET_SOV_FIELDS) == 17
    assert "Reference" in TARGET_SOV_FIELDS
    assert "Address" in TARGET_SOV_FIELDS
    assert "Building Value" in TARGET_SOV_FIELDS
    assert "Fire Sprinklers (Y/N)" in TARGET_SOV_FIELDS


def test_sheet_analysis_model():
    """Verify SheetAnalysis instantiation."""
    analysis = SheetAnalysis(
        sheet_name="Schedule of Locations",
        is_candidate=True,
        header_row=1,
        confidence=0.97,
        reasoning="Headers match property SOV signatures",
    )
    assert analysis.sheet_name == "Schedule of Locations"
    assert analysis.is_candidate is True
    assert analysis.confidence == 0.97


def test_schema_mapping_model():
    """Verify SchemaMapping instantiation."""
    mapping = SchemaMapping(
        source_column="Loc_Addr",
        target_field=TargetSOVField.ADDRESS.value,
        confidence=0.99,
        method="fuzzy_match",
        reasoning="Matched address variation",
    )
    assert mapping.source_column == "Loc_Addr"
    assert mapping.target_field == "Address"


def test_quality_issue_and_recommendation_models():
    """Verify QualityIssue and Recommendation instantiation."""
    issue = QualityIssue(
        row=5,
        field="Zip",
        issue="4 digit postal code",
        severity="warning",
        current_value="6060",
        recommendation="Pad with leading 0",
        confidence=0.98,
        reasoning="Standard 5-digit zip required",
    )
    assert issue.row == 5
    assert issue.severity == "warning"

    rec = Recommendation(
        row=5,
        field="Zip",
        action="fix_zip",
        current_value="6060",
        proposed_value="06060",
        confidence=0.98,
        reasoning="Prepended missing 0",
    )
    assert rec.proposed_value == "06060"


def test_review_decision_and_submission_models():
    """Verify ReviewDecision and batch ReviewSubmission."""
    decision = ReviewDecision(
        row=5,
        field="Zip",
        decision="approve",
        reviewer="tester@carrier.com",
    )
    assert decision.decision == "approve"
    assert isinstance(decision.timestamp, datetime)

    submission = ReviewSubmission(decisions=[decision], notes="Looks good")
    assert len(submission.decisions) == 1


def test_transformation_and_audit_models():
    """Verify Transformation and AuditEntry instantiation."""
    transformation = Transformation(
        row=5,
        field="Zip",
        before="6060",
        after="06060",
        transformation="fix_zip",
        approved_by="tester@carrier.com",
    )
    assert transformation.after == "06060"

    audit = AuditEntry(
        job_id="test-job-123",
        user_id="tester@carrier.com",
        action="transformation_applied",
        source="Zip",
        target="Zip",
        before="6060",
        after="06060",
    )
    assert audit.job_id == "test-job-123"


def test_shared_state_instantiation():
    """Verify SOVProcessingState creation and initial defaults."""
    file_info = FileInfo(
        filename="sov_test.xlsx",
        file_path="data/uploads/sov_test.xlsx",
        file_size_bytes=2048,
    )
    state = SOVProcessingState(
        job_id="job-uuid-123",
        file_info=file_info,
    )
    assert state.status == JobStatus.PENDING
    assert state.sheet_analysis == []
    assert state.schema_mappings == []
    assert state.recommendations == []
    assert state.review_decisions == []
    assert state.approved_transformations == []
    assert state.audit_log == []
