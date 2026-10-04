"""Test Pydantic models and data contracts."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models.sheet_models import SheetAnalysis
from app.models.schema_models import SchemaMapping, TARGET_SOV_FIELDS, TargetSOVField
from app.models.quality_models import QualityIssue, Recommendation
from app.models.review_models import (
    ReviewDecision,
    ReviewSubmission,
    DecisionType,
    ReviewRecommendation,
    FieldReviewDecision,
)
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


# ===========================================================================
# Member 3 integration tests — ReviewRecommendation and FieldReviewDecision
# ===========================================================================

class TestReviewRecommendation:
    """Tests for the ReviewRecommendation model (Member 3 integration)."""

    def test_valid_review_recommendation(self):
        """A fully populated ReviewRecommendation with valid confidence should pass."""
        rec = ReviewRecommendation(
            source_field="Building Value",
            target_field="total_insured_value",
            current_value="1,000,000",
            recommendation=1_000_000,
            confidence=0.95,
            reasoning="Value matches standard TIV format after stripping commas.",
        )
        assert rec.source_field == "Building Value"
        assert rec.target_field == "total_insured_value"
        assert rec.confidence == 0.95

    def test_review_recommendation_optional_fields_default_none(self):
        """current_value and recommendation are optional and default to None."""
        rec = ReviewRecommendation(
            source_field="Location",
            target_field="location_name",
            confidence=0.5,
            reasoning="Direct column match.",
        )
        assert rec.current_value is None
        assert rec.recommendation is None

    def test_review_recommendation_confidence_boundary_zero(self):
        """confidence = 0.0 is valid (minimum boundary)."""
        rec = ReviewRecommendation(
            source_field="f", target_field="t",
            confidence=0.0, reasoning="No idea.",
        )
        assert rec.confidence == 0.0

    def test_review_recommendation_confidence_boundary_one(self):
        """confidence = 1.0 is valid (maximum boundary)."""
        rec = ReviewRecommendation(
            source_field="f", target_field="t",
            confidence=1.0, reasoning="Perfect match.",
        )
        assert rec.confidence == 1.0

    def test_review_recommendation_invalid_confidence_above_one(self):
        """confidence > 1.0 must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRecommendation(
                source_field="f", target_field="t",
                confidence=1.5, reasoning="Over-confident agent.",
            )
        assert "confidence" in str(exc_info.value).lower()

    def test_review_recommendation_invalid_confidence_negative(self):
        """confidence < 0.0 must raise a ValidationError."""
        with pytest.raises(ValidationError):
            ReviewRecommendation(
                source_field="f", target_field="t",
                confidence=-0.1, reasoning="Negative confidence.",
            )


class TestFieldReviewDecision:
    """Tests for the FieldReviewDecision model (Member 3 integration)."""

    def test_valid_accept(self):
        """ACCEPT decision with no edited_value should pass."""
        decision = FieldReviewDecision(
            source_field="Building Value",
            target_field="total_insured_value",
            decision=DecisionType.ACCEPT,
            approver="alice",
        )
        assert decision.decision == DecisionType.ACCEPT
        assert decision.edited_value is None

    def test_valid_reject(self):
        """REJECT decision with no edited_value should pass."""
        decision = FieldReviewDecision(
            source_field="Building Value",
            target_field="total_insured_value",
            decision=DecisionType.REJECT,
            approver="bob",
        )
        assert decision.decision == DecisionType.REJECT
        assert decision.edited_value is None

    def test_valid_edit(self):
        """EDIT decision with an edited_value should pass."""
        decision = FieldReviewDecision(
            source_field="Building Value",
            target_field="total_insured_value",
            decision=DecisionType.EDIT,
            edited_value=2_000_000,
            approver="carol",
        )
        assert decision.decision == DecisionType.EDIT
        assert decision.edited_value == 2_000_000

    def test_edit_without_edited_value_fails(self):
        """EDIT decision with no edited_value must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            FieldReviewDecision(
                source_field="Building Value",
                target_field="total_insured_value",
                decision=DecisionType.EDIT,
                # edited_value intentionally omitted
                approver="carol",
            )
        assert "edited_value" in str(exc_info.value).lower()

    def test_empty_approver_fails(self):
        """An empty (or whitespace-only) approver must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            FieldReviewDecision(
                source_field="Building Value",
                target_field="total_insured_value",
                decision=DecisionType.ACCEPT,
                approver="   ",  # whitespace only — should be rejected
            )
        assert "approver" in str(exc_info.value).lower()

    def test_blank_approver_empty_string_fails(self):
        """An explicit empty string for approver must also fail."""
        with pytest.raises(ValidationError):
            FieldReviewDecision(
                source_field="f", target_field="t",
                decision=DecisionType.REJECT,
                approver="",
            )

    def test_accept_with_explicit_none_edited_value(self):
        """Explicitly passing edited_value=None for ACCEPT should be fine."""
        decision = FieldReviewDecision(
            source_field="f", target_field="t",
            decision=DecisionType.ACCEPT,
            edited_value=None,
            approver="dave",
        )
        assert decision.edited_value is None

    def test_decision_type_string_coercion(self):
        """Passing the string 'ACCEPT' should coerce to DecisionType.ACCEPT."""
        decision = FieldReviewDecision(
            source_field="f", target_field="t",
            decision="ACCEPT",  # plain string
            approver="eve",
        )
        assert decision.decision == DecisionType.ACCEPT

