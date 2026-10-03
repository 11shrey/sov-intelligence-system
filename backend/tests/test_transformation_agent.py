"""
tests/test_transformation_agent.py
-----------------------------------
Unit tests for Agent4, Normalizer, and TransformationResult
(Member 3 integration in transformation_agent.py).

Ported from member3_sov/tests/test_agent4.py.
Import mappings (standalone → integrated):
    app.agents.agent4               → app.agents.transformation_agent
    Recommendation                  → ReviewRecommendation
    ReviewDecision                  → FieldReviewDecision

Run with:  pytest tests/test_transformation_agent.py -v
"""

import copy

import pytest

from app.agents.transformation_agent import Agent4, Normalizer, TransformationResult
from app.models.review_models import (
    DecisionType,
    FieldReviewDecision,
    ReviewRecommendation,
)
from app.review.human_review import HumanReview


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_rec(
    source: str,
    target: str,
    recommendation: object = None,
    confidence: float = 0.9,
    current_value: object = None,
) -> ReviewRecommendation:
    return ReviewRecommendation(
        source_field=source,
        target_field=target,
        current_value=current_value,
        recommendation=recommendation,
        confidence=confidence,
        reasoning="Test recommendation.",
    )


def accept(rec: ReviewRecommendation, approver: str = "Tester") -> FieldReviewDecision:
    return HumanReview().accept(rec, approver=approver)


def reject(rec: ReviewRecommendation, approver: str = "Tester") -> FieldReviewDecision:
    return HumanReview().reject(rec, approver=approver)


def edit(
    rec: ReviewRecommendation, edited_value: object, approver: str = "Tester"
) -> FieldReviewDecision:
    return HumanReview().edit(rec, edited_value=edited_value, approver=approver)


@pytest.fixture
def agent() -> Agent4:
    return Agent4()


# ===========================================================================
# 1. ACCEPT — applies recommendation value to target field
# ===========================================================================

class TestAccept:

    def test_accept_writes_to_target_field(self, agent):
        """ACCEPT: recommendation value is written to target_field."""
        source = {"Bldg Repl Cost": "$1,250,000"}
        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="1250000")
        decision = accept(rec)

        result = agent.transform(source, [rec], [decision])

        assert "Building Value" in result.transformed_data

    def test_accept_applies_recommendation_value(self, agent):
        """ACCEPT: the target_field gets the recommendation's value (normalised)."""
        source = {"Bldg Repl Cost": "$1,250,000"}
        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="1250000")
        decision = accept(rec)

        result = agent.transform(source, [rec], [decision])

        assert result.transformed_data["Building Value"] == 1_250_000.0

    def test_accept_increments_applied_count(self, agent):
        """ACCEPT: applied_count is incremented by 1."""
        source = {}
        rec = make_rec("F", "G", recommendation="42")
        decision = accept(rec)

        result = agent.transform(source, [rec], [decision])

        assert result.applied_count == 1
        assert result.edited_count == 0
        assert result.rejected_count == 0
        assert result.pending_count == 0


# ===========================================================================
# 2. REJECT — does NOT apply recommendation
# ===========================================================================

class TestReject:

    def test_reject_does_not_write_to_target_field(self, agent):
        """REJECT: target_field must NOT appear in transformed_data."""
        source = {"Bldg Repl Cost": "$1,250,000"}
        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="1250000")
        decision = reject(rec)

        result = agent.transform(source, [rec], [decision])

        assert "Building Value" not in result.transformed_data

    def test_reject_is_not_treated_as_accept(self, agent):
        """REJECT: transformed_data must not contain the recommendation value."""
        source = {}
        rec = make_rec("Src", "Tgt", recommendation="secret_value")
        decision = reject(rec)

        result = agent.transform(source, [rec], [decision])

        assert result.transformed_data.get("Tgt") != "secret_value"

    def test_reject_increments_rejected_count(self, agent):
        """REJECT: rejected_count is incremented by 1."""
        source = {}
        rec = make_rec("F", "G", recommendation="val")
        decision = reject(rec)

        result = agent.transform(source, [rec], [decision])

        assert result.rejected_count == 1
        assert result.applied_count == 0


# ===========================================================================
# 3. EDIT — uses edited_value, not recommendation
# ===========================================================================

class TestEdit:

    def test_edit_writes_edited_value_to_target_field(self, agent):
        """EDIT: edited_value is written to target_field."""
        source = {"Fire Prot.": "YES"}
        rec = make_rec("Fire Prot.", "Fire Sprinklers (Y/N)", recommendation="Y")
        decision = edit(rec, edited_value="N")

        result = agent.transform(source, [rec], [decision])

        # Human chose "N", overriding the agent's "Y"
        assert result.transformed_data["Fire Sprinklers (Y/N)"] == "N"

    def test_edit_does_not_use_recommendation_value(self, agent):
        """EDIT: the recommendation value must NOT be used instead of edited_value."""
        source = {}
        rec = make_rec("Src", "Building Value", recommendation="999999")
        decision = edit(rec, edited_value="1000000")

        result = agent.transform(source, [rec], [decision])

        # Should be 1,000,000 (edited), not 999,999 (recommendation)
        assert result.transformed_data["Building Value"] == 1_000_000.0

    def test_edit_increments_edited_count(self, agent):
        """EDIT: edited_count is incremented by 1."""
        source = {}
        rec = make_rec("F", "G", recommendation="old")
        decision = edit(rec, edited_value="new")

        result = agent.transform(source, [rec], [decision])

        assert result.edited_count == 1
        assert result.applied_count == 0


# ===========================================================================
# 4. PENDING — no decision → field not applied
# ===========================================================================

class TestPending:

    def test_pending_does_not_apply_recommendation(self, agent):
        """PENDING (None decision): target_field must not appear."""
        source = {}
        rec = make_rec("Src", "Building Value", recommendation="1250000")

        result = agent.transform(source, [rec], [None])  # None = PENDING

        assert "Building Value" not in result.transformed_data

    def test_pending_is_never_auto_approved(self, agent):
        """A None decision must NEVER be treated as ACCEPT."""
        source = {}
        rec = make_rec("Src", "Building Value", recommendation="auto_approved_value")

        result = agent.transform(source, [rec], [None])

        assert result.transformed_data.get("Building Value") != "auto_approved_value"

    def test_pending_increments_pending_count(self, agent):
        """PENDING: pending_count is incremented by 1."""
        source = {}
        rec = make_rec("F", "G", recommendation="val")

        result = agent.transform(source, [rec], [None])

        assert result.pending_count == 1
        assert result.applied_count == 0
        assert result.rejected_count == 0


# ===========================================================================
# 5. Source data safety — original not modified
# ===========================================================================

class TestSourceDataSafety:

    def test_accept_does_not_modify_original_dict(self, agent):
        """ACCEPT: the original source_row dict is not mutated."""
        source = {"Bldg Repl Cost": "$1,250,000"}
        original_copy = copy.deepcopy(source)

        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="1250000")
        decision = accept(rec)
        agent.transform(source, [rec], [decision])

        assert source == original_copy

    def test_edit_does_not_modify_original_dict(self, agent):
        """EDIT: the original source_row dict is not mutated."""
        source = {"Fire Prot.": "YES", "other_field": "stays"}
        original_copy = copy.deepcopy(source)

        rec = make_rec("Fire Prot.", "Fire Sprinklers (Y/N)", recommendation="Y")
        decision = edit(rec, edited_value="N")
        agent.transform(source, [rec], [decision])

        assert source == original_copy

    def test_reject_does_not_modify_original_dict(self, agent):
        """REJECT: original dict is not mutated."""
        source = {"Bldg Repl Cost": "$1,250,000"}
        original_copy = copy.deepcopy(source)

        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="1250000")
        decision = reject(rec)
        agent.transform(source, [rec], [decision])

        assert source == original_copy


# ===========================================================================
# 6. Normalizer — currency
# ===========================================================================

class TestNormalizerCurrency:

    def test_dollar_with_commas(self):
        assert Normalizer.normalize_currency("$1,250,000") == 1_250_000.0

    def test_dollar_with_decimal(self):
        assert Normalizer.normalize_currency("$500,000.50") == 500_000.5

    def test_plain_number_string(self):
        assert Normalizer.normalize_currency("1250000") == 1_250_000.0

    def test_already_int(self):
        assert Normalizer.normalize_currency(1_250_000) == 1_250_000.0

    def test_already_float(self):
        assert Normalizer.normalize_currency(500_000.50) == 500_000.5

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            Normalizer.normalize_currency("not-a-number")


# ===========================================================================
# 7. Normalizer — sprinkler YES → Y
# ===========================================================================

class TestNormalizerSprinklerYes:

    @pytest.mark.parametrize("raw", ["YES", "Yes", "yes", "Y", "y"])
    def test_yes_variants_become_Y(self, raw):
        assert Normalizer.normalize_sprinkler(raw) == "Y"


# ===========================================================================
# 8. Normalizer — sprinkler NO → N
# ===========================================================================

class TestNormalizerSprinklerNo:

    @pytest.mark.parametrize("raw", ["NO", "No", "no", "N", "n"])
    def test_no_variants_become_N(self, raw):
        assert Normalizer.normalize_sprinkler(raw) == "N"

    def test_invalid_sprinkler_value_raises(self):
        with pytest.raises(ValueError):
            Normalizer.normalize_sprinkler("maybe")


# ===========================================================================
# 9. Normalizer — state normalization
# ===========================================================================

class TestNormalizerState:

    def test_massachusetts_becomes_MA(self):
        assert Normalizer.normalize_state("Massachusetts") == "MA"

    def test_lowercase_state(self):
        assert Normalizer.normalize_state("new york") == "NY"

    def test_already_abbreviated(self):
        assert Normalizer.normalize_state("TX") == "TX"

    def test_lowercase_abbreviated(self):
        assert Normalizer.normalize_state("ca") == "CA"

    def test_unknown_state_raises(self):
        with pytest.raises(ValueError):
            Normalizer.normalize_state("Atlantis")


# ===========================================================================
# 10. Field mismatch validation
# ===========================================================================

class TestFieldMismatch:

    def test_mismatched_source_field_raises(self, agent):
        """Decision with a different source_field must raise ValueError."""
        source = {}
        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="100")
        # Decision refers to a completely different field
        wrong_decision = FieldReviewDecision(
            source_field="Address",
            target_field="Building Value",
            decision=DecisionType.ACCEPT,
            approver="Tester",
        )
        with pytest.raises(ValueError, match="mismatch"):
            agent.transform(source, [rec], [wrong_decision])

    def test_mismatched_target_field_raises(self, agent):
        """Decision with a different target_field must raise ValueError."""
        source = {}
        rec = make_rec("Bldg Repl Cost", "Building Value", recommendation="100")
        wrong_decision = FieldReviewDecision(
            source_field="Bldg Repl Cost",
            target_field="City",           # wrong target
            decision=DecisionType.ACCEPT,
            approver="Tester",
        )
        with pytest.raises(ValueError, match="mismatch"):
            agent.transform(source, [rec], [wrong_decision])

    def test_length_mismatch_raises(self, agent):
        """Different lengths for recommendations and decisions must raise ValueError."""
        source = {}
        rec = make_rec("F", "G", recommendation="v")
        with pytest.raises(ValueError):
            agent.transform(source, [rec, rec], [accept(rec)])  # 2 recs, 1 decision


# ===========================================================================
# 11. Multiple recommendations in one transform call
# ===========================================================================

class TestMultipleRecommendations:

    def test_multiple_fields_transformed(self, agent):
        """Multiple ACCEPT decisions produce multiple target fields."""
        source = {
            "Bldg Repl Cost":  "$1,250,000",
            "Fire Prot.":      "YES",
            "State Name":      "Massachusetts",
        }
        rec1 = make_rec("Bldg Repl Cost", "Building Value",         recommendation="1250000")
        rec2 = make_rec("Fire Prot.",     "Fire Sprinklers (Y/N)",   recommendation="YES")
        rec3 = make_rec("State Name",     "Property State",          recommendation="Massachusetts")

        d1 = accept(rec1)
        d2 = accept(rec2)
        d3 = accept(rec3)

        result = agent.transform(source, [rec1, rec2, rec3], [d1, d2, d3])

        assert result.transformed_data["Building Value"] == 1_250_000.0
        assert result.transformed_data["Fire Sprinklers (Y/N)"] == "Y"
        assert result.transformed_data["Property State"] == "MA"
        assert result.applied_count == 3


# ===========================================================================
# 12. Mixed ACCEPT + EDIT + REJECT in one call
# ===========================================================================

class TestMixedDecisions:

    def test_accept_edit_reject_in_one_transform(self, agent):
        """
        Given three recommendations with ACCEPT / EDIT / REJECT decisions,
        only the ACCEPT and EDIT fields should appear in transformed_data.
        """
        source = {}

        rec_accept = make_rec("Bldg Repl Cost", "Building Value",       recommendation="1000000")
        rec_edit   = make_rec("Fire Prot.",     "Fire Sprinklers (Y/N)", recommendation="YES")
        rec_reject = make_rec("Unknown Field",  "Rejected Target",       recommendation="should_not_appear")

        d_accept = accept(rec_accept)
        d_edit   = edit(rec_edit, edited_value="N")
        d_reject = reject(rec_reject)

        result = agent.transform(
            source,
            [rec_accept, rec_edit, rec_reject],
            [d_accept,   d_edit,   d_reject],
        )

        # Counts
        assert result.applied_count  == 1
        assert result.edited_count   == 1
        assert result.rejected_count == 1
        assert result.pending_count  == 0

        # Data
        assert result.transformed_data["Building Value"]        == 1_000_000.0
        assert result.transformed_data["Fire Sprinklers (Y/N)"] == "N"
        assert "Rejected Target" not in result.transformed_data

    def test_accept_edit_reject_pending_combined(self, agent):
        """
        ACCEPT + EDIT + REJECT + PENDING all in one call.
        Only ACCEPT and EDIT fields appear; REJECT and PENDING are skipped.
        """
        source = {}

        rec1 = make_rec("F1", "Building Value",       recommendation="500000")
        rec2 = make_rec("F2", "Fire Sprinklers (Y/N)", recommendation="YES")
        rec3 = make_rec("F3", "Rejected Target",      recommendation="nope")
        rec4 = make_rec("F4", "Pending Target",       recommendation="not_yet")

        d1 = accept(rec1)
        d2 = edit(rec2, edited_value="N")
        d3 = reject(rec3)
        d4 = None  # PENDING

        result = agent.transform(source, [rec1, rec2, rec3, rec4], [d1, d2, d3, d4])

        assert result.applied_count  == 1
        assert result.edited_count   == 1
        assert result.rejected_count == 1
        assert result.pending_count  == 1

        assert result.transformed_data["Building Value"] == 500_000.0
        assert result.transformed_data["Fire Sprinklers (Y/N)"] == "N"
        assert "Rejected Target" not in result.transformed_data
        assert "Pending Target"  not in result.transformed_data

    def test_total_skipped_property(self, agent):
        """total_skipped == rejected_count + pending_count."""
        source = {}
        rec1 = make_rec("F1", "T1", recommendation="v1")
        rec2 = make_rec("F2", "T2", recommendation="v2")

        result = agent.transform(source, [rec1, rec2], [reject(rec1), None])

        assert result.total_skipped == 2


# ===========================================================================
# 13. ControlledTransformationAgent — smoke test (team class preserved)
# ===========================================================================

class TestControlledTransformationAgent:
    """Smoke tests confirming the team's ControlledTransformationAgent is intact."""

    def test_can_be_imported(self):
        """ControlledTransformationAgent must be importable from transformation_agent."""
        from app.agents.transformation_agent import ControlledTransformationAgent
        agent = ControlledTransformationAgent()
        assert agent is not None

    def test_run_produces_completed_state(self):
        """run() must set status to COMPLETED and set final_output_path."""
        from app.agents.transformation_agent import ControlledTransformationAgent
        from app.models.review_models import ReviewDecision
        from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus

        file_info = FileInfo(
            filename="test.xlsx",
            file_path="data/uploads/test.xlsx",
            file_size_bytes=1024,
        )
        state = SOVProcessingState(job_id="smoke-test-job", file_info=file_info)
        state.review_decisions.append(
            ReviewDecision(row=1, field="Zip", decision="approve", reviewer="tester")
        )

        agent = ControlledTransformationAgent()
        result_state = agent.run(state)

        assert result_state.status == JobStatus.COMPLETED
        assert result_state.final_output_path is not None
        assert len(result_state.approved_transformations) == 1
