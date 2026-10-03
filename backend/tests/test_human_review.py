"""
tests/test_human_review.py
--------------------------
Unit tests for the HumanReview service (Member 3 integration).

Ported from member3_sov/tests/test_human_review.py.
Class name mappings (standalone → integrated):
    Recommendation   → ReviewRecommendation
    ReviewDecision   → FieldReviewDecision

Run with:  pytest tests/test_human_review.py -v
"""

import pytest
from pydantic import ValidationError

from app.models.review_models import (
    DecisionType,
    FieldReviewDecision,
    ReviewRecommendation,
)
from app.review.human_review import HumanReview, ReviewSessionEntry


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_rec() -> ReviewRecommendation:
    """A standard ReviewRecommendation used across multiple tests."""
    return ReviewRecommendation(
        source_field="Bldg Repl Cost",
        target_field="Building Value",
        current_value="$1,250,000",
        recommendation="1250000",
        confidence=0.95,
        reasoning="Alias match — stripped currency symbol and commas.",
    )


@pytest.fixture
def hr() -> HumanReview:
    """A fresh HumanReview instance."""
    return HumanReview()


# ===========================================================================
# 1. ACCEPT
# ===========================================================================

class TestAccept:

    def test_accept_returns_field_review_decision(self, hr, sample_rec):
        """accept() must return a FieldReviewDecision instance."""
        decision = hr.accept(sample_rec, approver="Alice")
        assert isinstance(decision, FieldReviewDecision)

    def test_accept_decision_type(self, hr, sample_rec):
        """accept() must set decision to ACCEPT."""
        decision = hr.accept(sample_rec, approver="Alice")
        assert decision.decision == DecisionType.ACCEPT

    def test_accept_fields_copied_from_recommendation(self, hr, sample_rec):
        """accept() must copy source_field and target_field from the recommendation."""
        decision = hr.accept(sample_rec, approver="Alice")
        assert decision.source_field == sample_rec.source_field
        assert decision.target_field == sample_rec.target_field

    def test_accept_edited_value_is_none(self, hr, sample_rec):
        """accept() must always produce edited_value=None."""
        decision = hr.accept(sample_rec, approver="Alice")
        assert decision.edited_value is None

    def test_accept_approver_stored(self, hr, sample_rec):
        """accept() must preserve the approver name."""
        decision = hr.accept(sample_rec, approver="Alice")
        assert decision.approver == "Alice"


# ===========================================================================
# 2. REJECT
# ===========================================================================

class TestReject:

    def test_reject_returns_field_review_decision(self, hr, sample_rec):
        """reject() must return a FieldReviewDecision instance."""
        decision = hr.reject(sample_rec, approver="Bob")
        assert isinstance(decision, FieldReviewDecision)

    def test_reject_decision_type(self, hr, sample_rec):
        """reject() must set decision to REJECT."""
        decision = hr.reject(sample_rec, approver="Bob")
        assert decision.decision == DecisionType.REJECT

    def test_reject_edited_value_is_none(self, hr, sample_rec):
        """reject() must always produce edited_value=None."""
        decision = hr.reject(sample_rec, approver="Bob")
        assert decision.edited_value is None

    def test_reject_is_not_an_approved_transformation(self, hr, sample_rec):
        """
        A REJECT decision must NOT look like an approval.
        Agent 4 will skip any decision that is not ACCEPT or EDIT.
        """
        decision = hr.reject(sample_rec, approver="Bob")
        assert decision.decision != DecisionType.ACCEPT
        assert decision.decision != DecisionType.EDIT


# ===========================================================================
# 3. EDIT
# ===========================================================================

class TestEdit:

    def test_edit_returns_field_review_decision(self, hr, sample_rec):
        """edit() must return a FieldReviewDecision instance."""
        decision = hr.edit(sample_rec, edited_value=1_250_000, approver="Carol")
        assert isinstance(decision, FieldReviewDecision)

    def test_edit_decision_type(self, hr, sample_rec):
        """edit() must set decision to EDIT."""
        decision = hr.edit(sample_rec, edited_value=1_250_000, approver="Carol")
        assert decision.decision == DecisionType.EDIT

    def test_edit_stores_edited_value(self, hr, sample_rec):
        """edit() must store the supplied edited_value on the FieldReviewDecision."""
        decision = hr.edit(sample_rec, edited_value=1_250_000, approver="Carol")
        assert decision.edited_value == 1_250_000

    def test_edit_with_string_value(self, hr, sample_rec):
        """edited_value can be any type — strings are valid."""
        decision = hr.edit(sample_rec, edited_value="1250000", approver="Carol")
        assert decision.edited_value == "1250000"

    def test_edit_without_edited_value_raises_value_error(self, hr, sample_rec):
        """
        Calling edit() with edited_value=None must raise ValueError before
        a FieldReviewDecision is ever constructed.
        """
        with pytest.raises(ValueError, match="edited_value"):
            hr.edit(sample_rec, edited_value=None, approver="Carol")

    def test_edit_without_edited_value_does_not_create_decision(self, hr, sample_rec):
        """
        No FieldReviewDecision object should escape when edited_value is missing.
        The method must raise, not return an invalid object.
        """
        result = None
        try:
            result = hr.edit(sample_rec, edited_value=None, approver="Carol")
        except ValueError:
            pass
        assert result is None


# ===========================================================================
# 4. Approver validation
# ===========================================================================

class TestApproverValidation:

    def test_empty_approver_string_fails_on_accept(self, hr, sample_rec):
        """An empty approver must raise ValidationError on accept()."""
        with pytest.raises(ValidationError):
            hr.accept(sample_rec, approver="")

    def test_whitespace_only_approver_fails_on_accept(self, hr, sample_rec):
        """A whitespace-only approver must raise ValidationError on accept()."""
        with pytest.raises(ValidationError):
            hr.accept(sample_rec, approver="   ")

    def test_empty_approver_fails_on_reject(self, hr, sample_rec):
        """An empty approver must raise ValidationError on reject()."""
        with pytest.raises(ValidationError):
            hr.reject(sample_rec, approver="")

    def test_empty_approver_fails_on_edit(self, hr, sample_rec):
        """An empty approver must raise ValidationError on edit()."""
        with pytest.raises(ValidationError):
            hr.edit(sample_rec, edited_value=999, approver="")


# ===========================================================================
# 5. Source ReviewRecommendation not modified
# ===========================================================================

class TestImmutability:

    def test_accept_does_not_modify_recommendation(self, hr, sample_rec):
        """accept() must leave the original ReviewRecommendation completely unchanged."""
        original_source = sample_rec.source_field
        original_target = sample_rec.target_field
        original_value  = sample_rec.current_value
        original_rec    = sample_rec.recommendation
        original_conf   = sample_rec.confidence

        hr.accept(sample_rec, approver="Alice")

        assert sample_rec.source_field   == original_source
        assert sample_rec.target_field   == original_target
        assert sample_rec.current_value  == original_value
        assert sample_rec.recommendation == original_rec
        assert sample_rec.confidence     == original_conf

    def test_reject_does_not_modify_recommendation(self, hr, sample_rec):
        """reject() must leave the original ReviewRecommendation unchanged."""
        before = sample_rec.model_copy()
        hr.reject(sample_rec, approver="Bob")
        assert sample_rec == before

    def test_edit_does_not_modify_recommendation(self, hr, sample_rec):
        """edit() must leave the original ReviewRecommendation unchanged."""
        before = sample_rec.model_copy()
        hr.edit(sample_rec, edited_value=0, approver="Carol")
        assert sample_rec == before


# ===========================================================================
# 6. Multiple recommendations — session / batch
# ===========================================================================

class TestSession:

    def _make_rec(self, source: str) -> ReviewRecommendation:
        return ReviewRecommendation(
            source_field=source,
            target_field=f"std_{source.lower().replace(' ', '_')}",
            confidence=0.8,
            reasoning="Test recommendation.",
        )

    def test_session_initialised_with_multiple_recommendations(self):
        """HumanReview initialised with a list should track all entries as PENDING."""
        recs = [self._make_rec("Field A"), self._make_rec("Field B"), self._make_rec("Field C")]
        hr = HumanReview(recommendations=recs)
        assert len(hr.entries) == 3
        assert len(hr.pending) == 3
        assert len(hr.decided) == 0

    def test_accept_by_index(self):
        """accept_by_index() must record ACCEPT for that entry only."""
        recs = [self._make_rec("Field A"), self._make_rec("Field B")]
        hr = HumanReview(recommendations=recs)
        hr.accept_by_index(0, approver="Alice")
        assert hr.entries[0].decision is not None
        assert hr.entries[0].decision.decision == DecisionType.ACCEPT
        assert hr.entries[1].is_pending  # Field B still pending

    def test_reject_by_index(self):
        """reject_by_index() must record REJECT for that entry only."""
        recs = [self._make_rec("Field A"), self._make_rec("Field B")]
        hr = HumanReview(recommendations=recs)
        hr.reject_by_index(1, approver="Bob")
        assert hr.entries[1].decision.decision == DecisionType.REJECT
        assert hr.entries[0].is_pending  # Field A still pending

    def test_edit_by_index(self):
        """edit_by_index() must record EDIT with the correct edited_value."""
        recs = [self._make_rec("Field A")]
        hr = HumanReview(recommendations=recs)
        hr.edit_by_index(0, edited_value="corrected", approver="Carol")
        assert hr.entries[0].decision.decision == DecisionType.EDIT
        assert hr.entries[0].decision.edited_value == "corrected"

    def test_pending_entries_remain_pending(self):
        """Recommendations without an explicit decision must stay PENDING."""
        recs = [self._make_rec("F1"), self._make_rec("F2"), self._make_rec("F3")]
        hr = HumanReview(recommendations=recs)
        hr.accept_by_index(0, approver="Alice")
        hr.reject_by_index(2, approver="Alice")

        # F2 (index 1) has no decision
        assert hr.entries[1].is_pending
        assert len(hr.pending) == 1
        assert len(hr.decided) == 2

    def test_decisions_property_excludes_pending(self):
        """decisions property must only return FieldReviewDecision objects, not None."""
        recs = [self._make_rec("F1"), self._make_rec("F2")]
        hr = HumanReview(recommendations=recs)
        hr.accept_by_index(0, approver="Alice")
        decisions = hr.decisions
        assert len(decisions) == 1
        assert all(isinstance(d, FieldReviewDecision) for d in decisions)

    def test_add_recommendation_starts_pending(self):
        """Dynamically added recommendations start as PENDING."""
        hr = HumanReview()
        rec = self._make_rec("Dynamic Field")
        idx = hr.add_recommendation(rec)
        assert hr.entries[idx].is_pending

    def test_out_of_range_index_raises_index_error(self):
        """Accessing an invalid index must raise IndexError with a clear message."""
        hr = HumanReview(recommendations=[self._make_rec("F1")])
        with pytest.raises(IndexError):
            hr.accept_by_index(99, approver="Alice")


# ===========================================================================
# 7. Invalid decision type (belt-and-braces)
# ===========================================================================

class TestInvalidDecision:

    def test_invalid_decision_string_raises_validation_error(self, sample_rec):
        """
        Constructing a FieldReviewDecision with an unknown decision string
        must raise a ValidationError (Pydantic's enum coercion rejects it).
        """
        with pytest.raises(ValidationError):
            FieldReviewDecision(
                source_field=sample_rec.source_field,
                target_field=sample_rec.target_field,
                decision="MAYBE",      # not a valid DecisionType
                approver="Alice",
            )


# ===========================================================================
# 8. HumanReviewService (team class) — smoke test
# ===========================================================================

class TestHumanReviewService:
    """Smoke tests to confirm the team's HumanReviewService is still intact."""

    def test_service_can_be_imported(self):
        """HumanReviewService must be importable from the review module."""
        from app.review.human_review import HumanReviewService
        svc = HumanReviewService()
        assert svc is not None

    def test_record_decisions_updates_state(self):
        """record_decisions() must append decisions and set REVIEW_COMPLETED status."""
        from app.review.human_review import HumanReviewService
        from app.models.review_models import ReviewDecision, ReviewSubmission
        from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus

        svc = HumanReviewService()
        file_info = FileInfo(
            filename="test.xlsx",
            file_path="data/uploads/test.xlsx",
            file_size_bytes=1024,
        )
        state = SOVProcessingState(job_id="svc-test-job", file_info=file_info)
        submission = ReviewSubmission(
            decisions=[
                ReviewDecision(row=1, field="Zip", decision="approve", reviewer="tester")
            ]
        )
        updated_state = svc.record_decisions(state, submission)
        assert updated_state.status == JobStatus.REVIEW_COMPLETED
        assert len(updated_state.review_decisions) == 1
