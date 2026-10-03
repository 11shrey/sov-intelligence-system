"""
Integrated tests for Agent 3 (Data Quality & Reasoning) — adapted for the shared repository.

Tests the real implementation in app/agents/quality_agent.py using the shared
Pydantic contracts from app/models/quality_models.py.

Coverage:
  - Missing values (required and optional fields)
  - Invalid values/types (non-numeric strings)
  - Negative monetary values
  - Currency string parsing (e.g. "$1,500,000")
  - Duplicate detection (exact, normalized, fuzzy)
  - Year Built validation
  - Storeys validation
  - Fire Sprinklers validation
  - State/Country validation
  - Logical inconsistencies (TIV < Building Value)
  - Suspicious values (building value thresholds)
  - Recommendation generation
  - Severity ordering
  - Summary counts
  - Empty data handling
  - Input immutability
  - DataQualityAgent pipeline integration
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from app.agents.quality_agent import (
    analyze_quality,
    DataQualityAgent,
    QwenQualityAdapter,
    requires_human_review,
    should_invoke_qwen,
    CANONICAL_SOV_FIELDS,
)
from app.models.quality_models import (
    QualityIssue,
    QualityReport,
    IssueType,
    IssueSeverity,
)
from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _good_row(
    ref: str = "LOC-001",
    addr: str = "100 Main St",
    city: str = "Houston",
    state: str = "TX",
    zip_code: str = "77001",
    bv: Any = 5_000_000,
) -> dict[str, Any]:
    return {
        "Reference": ref,
        "Address": addr,
        "City": city,
        "State": state,
        "Zip": zip_code,
        "Building Value": bv,
        "Year Built": 2005,
        "Fire Sprinklers (Y/N)": "Y",
        "Storeys": 3,
    }


def _make_row(**kwargs) -> dict[str, Any]:
    return kwargs


# ===========================================================================
# 1. Missing value detection
# ===========================================================================

class TestMissingValueDetection:

    def test_missing_required_field_is_high_severity(self):
        rows = [_good_row()]
        rows[0]["Address"] = None
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Address" and i.issue_type == IssueType.missing_value.value
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.high.value

    def test_missing_optional_field_is_medium_severity(self):
        rows = [_good_row()]
        rows[0]["Contents"] = None
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Contents" and i.issue_type == IssueType.missing_value.value
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.medium.value

    def test_empty_string_detected_as_missing(self):
        rows = [_good_row()]
        rows[0]["Address"] = ""
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Address" and i.issue_type == IssueType.missing_value.value
        ]
        assert len(issues) >= 1

    def test_no_false_positive_on_good_row(self):
        rows = [_good_row()]
        report = analyze_quality(rows)
        missing = [
            i for i in report.issues
            if i.issue_type == IssueType.missing_value.value
        ]
        # Good row has required fields — none of them should be flagged missing
        assert all(
            i.field not in ("Reference", "Address", "City", "State", "Zip")
            for i in missing
        )

    def test_recommendation_present_for_missing_field(self):
        rows = [_good_row()]
        rows[0]["Reference"] = None
        report = analyze_quality(rows)
        issue = next(i for i in report.issues if i.field == "Reference")
        assert issue.recommendation and len(issue.recommendation) > 0


# ===========================================================================
# 2. Invalid value / type detection
# ===========================================================================

class TestInvalidNumericDetection:

    def test_non_numeric_string_in_building_value(self):
        rows = [_good_row()]
        rows[0]["Building Value"] = "N/A"
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Building Value" and i.issue_type == IssueType.invalid_numeric.value
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.high.value

    def test_negative_building_value_flagged(self):
        rows = [_good_row(bv=-500_000)]
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Building Value" and i.issue_type == IssueType.invalid_numeric.value
        ]
        assert len(issues) == 1

    def test_valid_numeric_no_issue(self):
        rows = [_good_row(bv=5_000_000)]
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Building Value" and i.issue_type == IssueType.invalid_numeric.value
        ]
        assert len(issues) == 0

    def test_currency_string_parsed_correctly(self):
        rows = [_good_row()]
        rows[0]["Building Value"] = "1,500,000.50"
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Building Value" and i.issue_type == IssueType.invalid_numeric.value
        ]
        assert len(issues) == 0


# ===========================================================================
# 3. Year Built validation
# ===========================================================================

class TestYearBuiltValidation:

    def test_year_too_old(self):
        rows = [_good_row()]
        rows[0]["Year Built"] = 1200
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Year Built" and i.issue_type == IssueType.invalid_year.value
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.medium.value

    def test_year_in_future(self):
        rows = [_good_row()]
        rows[0]["Year Built"] = 2999
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Year Built" and i.issue_type == IssueType.invalid_year.value
        ]
        assert len(issues) == 1

    def test_non_numeric_year(self):
        rows = [_good_row()]
        rows[0]["Year Built"] = "UNKNOWN"
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Year Built" and i.issue_type == IssueType.invalid_year.value
        ]
        assert len(issues) == 1

    def test_valid_year_no_issue(self):
        rows = [_good_row()]
        rows[0]["Year Built"] = 1998
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Year Built" and i.issue_type == IssueType.invalid_year.value
        ]
        assert len(issues) == 0


# ===========================================================================
# 4. Storeys validation
# ===========================================================================

class TestStoreysValidation:

    def test_fractional_storeys_flagged(self):
        rows = [_good_row()]
        rows[0]["Storeys"] = 5.5
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Storeys" and i.issue_type == IssueType.invalid_value.value
        ]
        assert len(issues) == 1

    def test_whole_number_storeys_ok(self):
        rows = [_good_row()]
        rows[0]["Storeys"] = 3
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Storeys" and i.issue_type == IssueType.invalid_value.value
        ]
        assert len(issues) == 0


# ===========================================================================
# 5. Duplicate detection
# ===========================================================================

class TestDuplicateDetection:

    def test_exact_duplicate(self):
        row_a = _good_row(ref="LOC-001", addr="100 Main St")
        row_b = _good_row(ref="LOC-001", addr="100 Main St")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 1
        assert "exact duplicate" in dups[0].reasoning
        assert dups[0].severity == IssueSeverity.high.value

    def test_different_refs_no_duplicate(self):
        row_a = _good_row(ref="LOC-001", addr="100 Main St")
        row_b = _good_row(ref="LOC-002", addr="100 Main St")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 0

    def test_normalized_abbreviation_duplicate(self):
        row_a = _good_row(ref="LOC-001", addr="123 Main St")
        row_b = _good_row(ref="LOC-001", addr="123 Main Street")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 1
        assert "normalized" in dups[0].reasoning

    def test_fuzzy_minor_typo(self):
        row_a = _good_row(ref="LOC-001", addr="123 Main Street")
        row_b = _good_row(ref="LOC-001", addr="123 Main Stret")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 1
        assert "possible duplicate" in dups[0].reasoning

    def test_different_numeric_component_not_duplicate(self):
        row_a = _good_row(ref="LOC-001", addr="123 Main Street")
        row_b = _good_row(ref="LOC-001", addr="125 Main Street")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 0

    def test_different_unit_not_duplicate(self):
        row_a = _good_row(ref="LOC-001", addr="12 Park Road Unit 4")
        row_b = _good_row(ref="LOC-001", addr="12 Park Road Unit 7")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 0

    def test_completely_different_addresses_not_duplicate(self):
        row_a = _good_row(ref="LOC-001", addr="123 Main Street")
        row_b = _good_row(ref="LOC-001", addr="900 Oak Avenue")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 0

    def test_multiple_duplicate_groups(self):
        row1 = _good_row(ref="L1", addr="A")
        row2 = _good_row(ref="L1", addr="A")
        row3 = _good_row(ref="L2", addr="B")
        row4 = _good_row(ref="L2", addr="B")
        report = analyze_quality([row1, row2, row3, row4])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 2

    def test_missing_reference_skips_duplicate_check(self):
        row_a = _good_row(ref="", addr="123 Main Street")
        row_b = _good_row(ref="", addr="123 Main Street")
        report = analyze_quality([row_a, row_b])
        dups = [i for i in report.issues if i.issue_type == IssueType.duplicate_record.value]
        assert len(dups) == 0


# ===========================================================================
# 6. Fire Sprinklers validation
# ===========================================================================

class TestFireSprinklersValidation:

    def test_invalid_sprinkler_maybe(self):
        rows = [_good_row()]
        rows[0]["Fire Sprinklers (Y/N)"] = "MAYBE"
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Fire Sprinklers (Y/N)" and i.issue_type == IssueType.invalid_sprinkler.value
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.medium.value

    @pytest.mark.parametrize("valid_val", ["Y", "N", "Y13", "Y(13R)", "y", "n", "y13", "Y (13R)"])
    def test_valid_sprinkler_values(self, valid_val: str):
        """Authoritative allowed values are: Y, N, Y13, Y(13R) (case/whitespace normalized)."""
        rows = [_good_row()]
        rows[0]["Fire Sprinklers (Y/N)"] = valid_val
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Fire Sprinklers (Y/N)" and i.issue_type == IssueType.invalid_sprinkler.value
        ]
        assert len(issues) == 0

    @pytest.mark.parametrize("invalid_val", ["YES", "NO", "1", "0", "99", "TRUE", "FALSE"])
    def test_unsupported_sprinkler_values_flagged(self, invalid_val: str):
        """Values outside {Y, N, Y13, Y(13R)} must be reported as invalid."""
        rows = [_good_row()]
        rows[0]["Fire Sprinklers (Y/N)"] = invalid_val
        report = analyze_quality(rows)
        issues = [
            i for i in report.issues
            if i.field == "Fire Sprinklers (Y/N)" and i.issue_type == IssueType.invalid_sprinkler.value
        ]
        assert len(issues) == 1


# ===========================================================================
# 7. State/Country validation
# ===========================================================================

class TestStateCountryValidation:

    def test_valid_state_code(self):
        rows = [_good_row()]
        rows[0]["State"] = "TX"
        report = analyze_quality(rows)
        assert len([i for i in report.issues if i.field == "State"]) == 0

    def test_invalid_state_full_name(self):
        rows = [_good_row()]
        rows[0]["State"] = "Texas"
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "State"]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.medium.value

    def test_valid_country(self):
        rows = [_good_row()]
        rows[0]["Country"] = "USA"
        report = analyze_quality(rows)
        assert len([i for i in report.issues if i.field == "Country"]) == 0

    def test_invalid_country(self):
        rows = [_good_row()]
        rows[0]["Country"] = "Narnia"
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Country"]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.low.value


# ===========================================================================
# 8. Schema Conformance: No Invented Cross-Field Rules
# ===========================================================================

class TestSchemaConformanceNoInventedCrossFieldRules:

    def test_no_cross_field_contents_vs_building_value_rule(self):
        """Contents exceeding Building Value is not an error because no cross-field rule exists."""
        rows = [_good_row(bv=1_000_000)]
        rows[0]["Contents"] = 20_000_000  # Higher than Building Value
        report = analyze_quality(rows)
        # No cross-field error between Contents and Building Value
        assert len([i for i in report.issues if i.issue_type == IssueType.suspicious_value.value]) == 0

    def test_legacy_fields_ignored_and_not_substituted(self):
        """Legacy fields like Total Insured Value or Square Footage are not part of canonical schema."""
        rows = [_good_row()]
        rows[0]["Total Insured Value"] = 1_000
        rows[0]["Square Footage"] = 50
        report = analyze_quality(rows)
        # Agent 3 strictly operates on the 17 canonical fields and does not validate legacy fields
        assert all(i.field not in ("Total Insured Value", "Square Footage") for i in report.issues)


# ===========================================================================
# 9. No Historical Thresholds & Zero Allowance
# ===========================================================================

class TestNoHistoricalThresholdsAndZeroAllowed:

    def test_low_building_value_not_flagged(self):
        """No historical thresholds: a low building value is not proof that it is invalid."""
        rows = [_good_row(bv=500)]
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Building Value"]
        assert len(issues) == 0

    def test_zero_building_value_is_allowed(self):
        """Zero must not automatically be treated as invalid solely because it is zero."""
        rows = [_good_row(bv=0)]
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Building Value"]
        assert len(issues) == 0

    def test_zero_contents_bi_other_allowed(self):
        """Zero is explicitly allowed for Contents, BI, and Other."""
        rows = [_good_row()]
        rows[0]["Contents"] = 0
        rows[0]["BI"] = 0
        rows[0]["Other"] = 0
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field in ("Contents", "BI", "Other")]
        assert len(issues) == 0

    def test_large_building_value_not_flagged_by_arbitrary_threshold(self):
        """Values are not flagged solely for being unusually large without historical dataset."""
        rows = [_good_row(bv=15_000_000_000)]
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Building Value"]
        assert len(issues) == 0


# ===========================================================================
# 9b. Zip, Occupancy, Construction, Integer Validation
# ===========================================================================

class TestFieldSpecificValidations:

    def test_negative_zip_flagged(self):
        rows = [_good_row()]
        rows[0]["Zip"] = -77001
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Zip"]
        assert len(issues) == 1

    def test_valid_zip_with_leading_zero_string(self):
        rows = [_good_row()]
        rows[0]["Zip"] = "07030"
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Zip"]
        assert len(issues) == 0

    def test_negative_storeys_flagged(self):
        rows = [_good_row()]
        rows[0]["Storeys"] = -2
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Storeys"]
        assert len(issues) == 1

    def test_negative_number_of_buildings_flagged(self):
        rows = [_good_row()]
        rows[0]["Number of Buildings"] = -1
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Number of Buildings"]
        assert len(issues) == 1

    def test_numeric_occupancy_flagged(self):
        rows = [_good_row()]
        rows[0]["Occupancy"] = "99999"
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Occupancy"]
        assert len(issues) == 1

    def test_monetary_construction_flagged(self):
        rows = [_good_row()]
        rows[0]["Construction"] = "$1,500,000"
        report = analyze_quality(rows)
        issues = [i for i in report.issues if i.field == "Construction"]
        assert len(issues) == 1


# ===========================================================================
# 10. Recommendation generation
# ===========================================================================

class TestRecommendationGeneration:

    def test_all_issues_have_recommendation(self):
        messy = {
            "Reference": None,
            "Address": "",
            "State": "Texas",
            "Building Value": -100,
            "Year Built": 1100,
            "Fire Sprinklers (Y/N)": "MAYBE",
        }
        report = analyze_quality([messy])
        for issue in report.issues:
            assert issue.recommendation and len(issue.recommendation) > 0

    def test_all_issues_have_reasoning(self):
        messy = {
            "Reference": None,
            "Building Value": "N/A",
        }
        report = analyze_quality([messy])
        for issue in report.issues:
            assert issue.reasoning and len(issue.reasoning) > 0


# ===========================================================================
# 11. Severity ordering and summary
# ===========================================================================

class TestSeverityOrderingAndSummary:

    def test_severity_ordering_high_before_medium_before_low(self):
        messy = {
            "Reference": None,          # high (required missing)
            "Building Value": "N/A",    # high (invalid numeric)
            "Year Built": 1100,         # medium
        }
        report = analyze_quality([messy])
        _sev_rank = {"high": 0, "error": 0, "critical": 0, "medium": 1, "warning": 1, "low": 2, "info": 2}
        sevs = [_sev_rank.get(i.severity, 3) for i in report.issues]
        assert sevs == sorted(sevs)

    def test_summary_counts(self):
        rows = [_good_row(), _good_row()]  # exact duplicate
        report = analyze_quality(rows)
        assert IssueType.duplicate_record.value in report.summary

    def test_total_rows_scanned_correct(self):
        rows = [_good_row(), _good_row(ref="LOC-002")]
        report = analyze_quality(rows)
        assert report.total_rows_scanned == 2

    def test_total_issues_count_matches(self):
        rows = [_good_row()]
        rows[0]["Reference"] = None
        report = analyze_quality(rows)
        assert report.total_issues == len(report.issues)


# ===========================================================================
# 12. Edge cases
# ===========================================================================

class TestEdgeCases:

    def test_empty_data_returns_zero_issues(self):
        report = analyze_quality([])
        assert report.total_issues == 0
        assert report.total_rows_scanned == 0

    def test_input_data_not_modified(self):
        original = _good_row()
        original["Building Value"] = "N/A"
        before = copy.deepcopy(original)
        analyze_quality([original])
        assert original == before

    def test_report_structure_complete(self):
        report = analyze_quality([_good_row()])
        assert hasattr(report, "total_rows_scanned")
        assert hasattr(report, "total_issues")
        assert hasattr(report, "issues")
        assert hasattr(report, "recommendations")
        assert hasattr(report, "summary")


# ===========================================================================
# 13. DataQualityAgent pipeline integration
# ===========================================================================

class TestDataQualityAgentPipeline:

    def test_agent_instantiation(self):
        agent = DataQualityAgent()
        assert agent is not None

    def test_agent_run_with_mapped_rows(self):
        fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
        state = SOVProcessingState(job_id="test-job", file_info=fi)
        state.metadata["mapped_rows"] = [
            _good_row(),
            _good_row(ref="LOC-002", addr="200 Oak Ave", bv=2_000_000),
        ]
        agent = DataQualityAgent()
        updated_state = agent.run(state)
        assert updated_state.status == JobStatus.AWAITING_REVIEW

    def test_agent_run_detects_missing_field(self):
        fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
        state = SOVProcessingState(job_id="test-job", file_info=fi)
        row = _good_row()
        row["Reference"] = None
        state.metadata["mapped_rows"] = [row]
        agent = DataQualityAgent()
        updated_state = agent.run(state)
        assert updated_state.status == JobStatus.AWAITING_REVIEW
        issues = [
            i for i in updated_state.quality_issues
            if i.field == "Reference" and i.issue_type == IssueType.missing_value.value
        ]
        assert len(issues) >= 1

    def test_agent_run_no_mapped_rows_safe(self):
        """Agent must not crash when mapped_rows is absent from state."""
        fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
        state = SOVProcessingState(job_id="test-job", file_info=fi)
        agent = DataQualityAgent()
        updated_state = agent.run(state)
        assert updated_state.status == JobStatus.AWAITING_REVIEW

    def test_agent_does_not_modify_source_data(self):
        fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
        state = SOVProcessingState(job_id="test-job", file_info=fi)
        row = _good_row()
        row["Building Value"] = "N/A"
        original_row = copy.deepcopy(row)
        state.metadata["mapped_rows"] = [row]
        agent = DataQualityAgent()
        agent.run(state)
        assert row == original_row


# ===========================================================================
# 14. Qwen Contextual Reasoning & Human-Review Routing Policy (22 Requirements)
# ===========================================================================

class TestQwenContextualReasoningAndRoutingPolicy:

    def test_1_clean_row_does_not_call_qwen(self):
        """Clean row with standard values must not call Qwen."""
        qwen_called = False

        def mock_llm(payload):
            nonlocal qwen_called
            qwen_called = True
            return {"severity": "low", "reasoning": "Should not be called", "recommendation": "N/A"}

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Office"
        row["Construction"] = "Masonry"
        report = analyze_quality([row], llm_adapter=adapter)
        assert not qwen_called
        assert len(report.issues) == 0

    def test_2_valid_financial_values_do_not_call_qwen(self):
        """Valid financial values must never trigger Qwen."""
        qwen_called = False

        def mock_llm(payload):
            nonlocal qwen_called
            qwen_called = True
            return {"severity": "low", "reasoning": "N/A", "recommendation": "N/A"}

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row(bv=10_000_000)
        row["Contents"] = 2_500_000
        row["BI"] = 1_000_000
        row["Other"] = 500_000
        report = analyze_quality([row], llm_adapter=adapter)
        assert not qwen_called

    def test_3_missing_required_value_uses_deterministic_reasoning(self):
        """Missing required value uses deterministic reasoning without calling Qwen."""
        qwen_called = False

        def mock_llm(payload):
            nonlocal qwen_called
            qwen_called = True
            return None

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Address"] = None
        report = analyze_quality([row], llm_adapter=adapter)
        assert not qwen_called
        issue = next(i for i in report.issues if i.field == "Address")
        assert issue.reasoning_source == "deterministic"
        assert not issue.qwen_used
        assert issue.requires_human_review is True

    def test_4_invalid_numeric_value_uses_deterministic_reasoning(self):
        """Invalid numeric value uses deterministic reasoning without calling Qwen."""
        qwen_called = False

        def mock_llm(payload):
            nonlocal qwen_called
            qwen_called = True
            return None

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Building Value"] = "INVALID_NUMBER"
        report = analyze_quality([row], llm_adapter=adapter)
        assert not qwen_called
        issue = next(i for i in report.issues if i.field == "Building Value")
        assert issue.reasoning_source == "deterministic"
        assert not issue.qwen_used
        assert issue.requires_human_review is True

    def test_5_invalid_sprinkler_value_uses_deterministic_reasoning(self):
        """Invalid sprinkler value uses deterministic reasoning without calling Qwen."""
        qwen_called = False

        def mock_llm(payload):
            nonlocal qwen_called
            qwen_called = True
            return None

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Fire Sprinklers (Y/N)"] = "UNKNOWN_VAL"
        report = analyze_quality([row], llm_adapter=adapter)
        assert not qwen_called
        issue = next(i for i in report.issues if i.field == "Fire Sprinklers (Y/N)")
        assert issue.reasoning_source == "deterministic"
        assert not issue.qwen_used

    def test_6_negative_storeys_uses_deterministic_reasoning(self):
        """Negative Storeys uses deterministic reasoning without calling Qwen."""
        qwen_called = False

        def mock_llm(payload):
            nonlocal qwen_called
            qwen_called = True
            return None

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Storeys"] = -5
        report = analyze_quality([row], llm_adapter=adapter)
        assert not qwen_called
        issue = next(i for i in report.issues if i.field == "Storeys")
        assert issue.reasoning_source == "deterministic"
        assert not issue.qwen_used

    def test_7_ambiguous_occupancy_can_invoke_qwen(self):
        """Ambiguous or non-standard Occupancy invokes Qwen contextual reasoning."""
        qwen_invoked = False

        def mock_llm(payload):
            nonlocal qwen_invoked
            qwen_invoked = True
            assert payload["field"] == "Occupancy"
            return {
                "severity": "medium",
                "reasoning": "Non-standard occupancy description requires underwriter clarification.",
                "recommendation": "Verify Occupancy against policy schedule documents.",
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Specialized cryogenic research cleanroom facility"
        report = analyze_quality([row], llm_adapter=adapter)
        assert qwen_invoked
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.reasoning_source == "qwen"
        assert issue.qwen_used is True
        assert issue.severity == "medium"
        assert issue.requires_human_review is True

    def test_8_ambiguous_construction_can_invoke_qwen(self):
        """Ambiguous or non-standard Construction invokes Qwen contextual reasoning."""
        qwen_invoked = False

        def mock_llm(payload):
            nonlocal qwen_invoked
            qwen_invoked = True
            assert payload["field"] == "Construction"
            return {
                "severity": "high",
                "reasoning": "Uncommon modular composite construction material poses unknown fire risk.",
                "recommendation": "Obtain structural engineering survey for construction material.",
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Construction"] = "Hybrid structural insulated sandwich panel composite"
        report = analyze_quality([row], llm_adapter=adapter)
        assert qwen_invoked
        issue = next(i for i in report.issues if i.field == "Construction")
        assert issue.reasoning_source == "qwen"
        assert issue.qwen_used is True
        assert issue.severity == "high"
        assert issue.requires_human_review is True

    def test_9_qwen_returns_valid_json(self):
        """Qwen structured output is parsed into QualityIssue fields."""
        def mock_llm(payload):
            return {
                "severity": "low",
                "reasoning": "Recognizable secondary occupancy term.",
                "recommendation": "Confirm whether secondary occupancy is ancillary.",
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Incidental storage mezzanine"
        report = analyze_quality([row], llm_adapter=adapter)
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.severity == "low"
        assert "Recognizable secondary occupancy" in issue.reasoning
        assert "Confirm whether secondary occupancy" in issue.recommendation

    def test_10_qwen_malformed_json_does_not_crash(self):
        """Malformed JSON from Qwen does not crash Agent 3 and uses safe fallback."""
        def mock_llm(payload):
            return "This is not valid json { foo: bar "

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Exotic flex space structure"
        report = analyze_quality([row], llm_adapter=adapter)
        assert len(report.issues) == 1
        issue = report.issues[0]
        assert issue.reasoning_source == "qwen_fallback"
        assert not issue.qwen_used
        assert issue.requires_human_review is True

    def test_11_qwen_timeout_does_not_crash(self):
        """Qwen timeout does not crash Agent 3 and falls back gracefully."""
        def mock_llm(payload):
            raise TimeoutError("Qwen connection timed out")

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Unknown occupancy code 882"
        report = analyze_quality([row], llm_adapter=adapter)
        assert len(report.issues) == 1
        issue = report.issues[0]
        assert issue.reasoning_source == "qwen_fallback"
        assert not issue.qwen_used

    def test_12_qwen_cannot_provide_a_replacement_value(self):
        """Qwen is advisory only; proposed_value must strictly be None."""
        def mock_llm(payload):
            return {
                "severity": "medium",
                "reasoning": "Should probably be Commercial Office.",
                "recommendation": "Verify against policy records.",
                "proposed_value": "Commercial Office",  # Unauthorized key attempt
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Ambiguous business center"
        report = analyze_quality([row], llm_adapter=adapter)
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.proposed_value is None
        rec = next(r for r in report.recommendations if r.field == "Occupancy")
        assert rec.proposed_value is None

    def test_13_qwen_severity_low_does_not_require_human_review(self):
        """Deterministic routing: low severity does NOT require human review."""
        def mock_llm(payload):
            return {
                "severity": "low",
                "reasoning": "Minor non-standard terminology.",
                "recommendation": "Log only.",
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Ancillary retail kiosk"
        report = analyze_quality([row], llm_adapter=adapter)
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.severity == "low"
        assert issue.requires_human_review is False
        assert requires_human_review("low") is False

    def test_14_qwen_severity_medium_requires_human_review(self):
        """Deterministic routing: medium severity DOES require human review."""
        def mock_llm(payload):
            return {
                "severity": "medium",
                "reasoning": "Ambiguous occupancy may impact rate classification.",
                "recommendation": "Review source policy schedule.",
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Co-working tech incubator"
        report = analyze_quality([row], llm_adapter=adapter)
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.severity == "medium"
        assert issue.requires_human_review is True
        assert requires_human_review("medium") is True

    def test_15_qwen_severity_high_requires_human_review(self):
        """Deterministic routing: high severity DOES require human review."""
        def mock_llm(payload):
            return {
                "severity": "high",
                "reasoning": "High-risk unclassified manufacturing process.",
                "recommendation": "Obtain loss prevention inspection report.",
            }

        adapter = QwenQualityAdapter(llm_callable=mock_llm)
        row = _good_row()
        row["Occupancy"] = "Hazardous chemical synthesizer facility"
        report = analyze_quality([row], llm_adapter=adapter)
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.severity == "high"
        assert issue.requires_human_review is True
        assert requires_human_review("high") is True

    def test_16_passing_fields_remain_unchanged(self):
        """Fields and rows that pass validation must remain completely unchanged."""
        row = _good_row(ref="REF-999", addr="555 Oak St", bv=450000)
        row["Occupancy"] = "Office"
        row["Construction"] = "Masonry"
        before = copy.deepcopy(row)
        analyze_quality([row])
        assert row["Building Value"] == 450000
        assert row["Reference"] == "REF-999"
        assert row["Address"] == "555 Oak St"
        assert row == before

    def test_17_missing_values_remain_missing(self):
        """Agent 3 never automatically fills, interpolates, or replaces missing values."""
        row = _good_row()
        row["Contents"] = None
        row["Other"] = None
        before = copy.deepcopy(row)
        analyze_quality([row])
        assert row["Contents"] is None
        assert row["Other"] is None
        assert row == before

    def test_18_exactly_17_canonical_fields_remain_present(self):
        """Agent 3 operates on exactly 17 canonical fields in authoritative order."""
        assert len(CANONICAL_SOV_FIELDS) == 17
        expected = [
            "Reference", "Address", "City", "State", "Zip", "County", "Country",
            "Building Value", "Contents", "BI", "Occupancy", "Construction",
            "Storeys", "Number of Buildings", "Year Built", "Fire Sprinklers (Y/N)", "Other",
        ]
        assert CANONICAL_SOV_FIELDS == expected

    def test_19_no_legacy_fields_are_introduced(self):
        """Legacy fields (Location Name, Contents Value, Total Insured Value, Square Footage, Number of Stories) must not be in canonical schema."""
        legacy = [
            "Location Name", "Contents Value", "Total Insured Value",
            "Square Footage", "Number of Stories",
        ]
        for leg in legacy:
            assert leg not in CANONICAL_SOV_FIELDS

    def test_20_qwen_failure_uses_deterministic_fallback(self):
        """Qwen returning None triggers safe deterministic fallback with qwen_fallback source."""
        adapter = QwenQualityAdapter(llm_callable=lambda p: None)
        row = _good_row()
        row["Occupancy"] = "Ambiguous warehouse depot"
        report = analyze_quality([row], llm_adapter=adapter)
        issue = next(i for i in report.issues if i.field == "Occupancy")
        assert issue.reasoning_source == "qwen_fallback"
        assert not issue.qwen_used
        assert issue.requires_human_review is True
        assert issue.proposed_value is None

    def test_21_no_arbitrary_financial_thresholds_introduced(self):
        """No arbitrary financial thresholds (e.g. Building Value < X or > X) are flagged."""
        row_low = _good_row(bv=250)
        report_low = analyze_quality([row_low])
        assert len([i for i in report_low.issues if i.field == "Building Value"]) == 0

        row_high = _good_row(bv=25_000_000_000)
        report_high = analyze_quality([row_high])
        assert len([i for i in report_high.issues if i.field == "Building Value"]) == 0

    def test_22_no_cross_field_consistency_rules_introduced(self):
        """No invented cross-field relationships are enforced."""
        row = _good_row(bv=1_000_000)
        row["Contents"] = 50_000_000  # Contents > Building Value is permitted
        report = analyze_quality([row])
        assert len([i for i in report.issues if i.issue_type == IssueType.suspicious_value.value]) == 0

