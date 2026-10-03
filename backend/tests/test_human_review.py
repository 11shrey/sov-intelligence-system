"""Tests for HumanReviewService routing policy.

Verifies:
1. LOW issue -> appears in audit information but NOT in human-review inbox.
2. MEDIUM issue -> appears in human-review inbox.
3. HIGH issue -> appears in human-review inbox.
4. Dataset containing LOW + MEDIUM issues -> returns only the MEDIUM issue in pending human-review queue.
5. Clean dataset -> produces no human-review items.
"""

from app.models.quality_models import IssueSeverity, IssueType, QualityIssue, Recommendation
from app.orchestration.orchestrator import PipelineOrchestrator
from app.orchestration.state import FileInfo, JobStatus, SOVProcessingState
from app.review.human_review import HumanReviewService


_CLEAN_ROW = {
    "Reference": "LOC-001",
    "Address": "100 Main St",
    "City": "Houston",
    "State": "TX",
    "Zip": "77001",
    "County": "Harris",
    "Country": "USA",
    "Building Value": 5_000_000,
    "Contents": 500_000,
    "BI": 200_000,
    "Occupancy": "Office",
    "Construction": "Masonry",
    "Storeys": 4,
    "Number of Buildings": 1,
    "Year Built": 2010,
    "Fire Sprinklers (Y/N)": "Y",
    "Other": 50_000,
}


def _create_sample_state(job_id: str = "job-test-1") -> SOVProcessingState:
    return SOVProcessingState(
        job_id=job_id,
        file_info=FileInfo(
            filename="portfolio.xlsx",
            file_path="data/uploads/portfolio.xlsx",
            file_size_bytes=1024,
        ),
    )


def test_low_issue_in_audit_but_not_in_human_review():
    """LOW issue -> appears in audit information but NOT in human-review inbox."""
    service = HumanReviewService()
    state = _create_sample_state("job-low-test")

    low_issue = QualityIssue(
        row=1,
        field="County",
        issue="Field 'County' is empty.",
        severity=IssueSeverity.low.value,
        current_value=None,
        recommendation="Provide County from source records if available.",
        reasoning="County is missing in row 1.",
        issue_type=IssueType.missing_value.value,
        requires_human_review=False,
        reasoning_source="deterministic",
        qwen_used=False,
        proposed_value=None,
    )
    rec = Recommendation(
        row=1,
        field="County",
        action="supply_county",
        current_value=None,
        proposed_value=None,
        confidence=1.0,
        reasoning="County is missing in row 1.",
    )

    state.quality_issues.append(low_issue)
    state.recommendations.append(rec)

    # Audit records all detected issues
    assert len(state.quality_issues) == 1
    assert state.quality_issues[0].severity == "low"
    assert state.quality_issues[0].requires_human_review is False

    # Pending human review items filter out LOW issues
    pending = service.get_pending_review_items(state)
    assert len(pending["quality_issues"]) == 0
    assert len(pending["recommendations"]) == 0


def test_medium_issue_in_human_review():
    """MEDIUM issue -> appears in human-review inbox."""
    service = HumanReviewService()
    state = _create_sample_state("job-medium-test")

    med_issue = QualityIssue(
        row=1,
        field="State",
        issue="'XX' is not a recognized US or Canadian state/province code.",
        severity=IssueSeverity.medium.value,
        current_value="XX",
        recommendation="Confirm the state or province code with the source submission.",
        reasoning="State 'XX' in row 1 is unrecognized.",
        issue_type=IssueType.inconsistent_value.value,
        requires_human_review=True,
        reasoning_source="deterministic",
        qwen_used=False,
        proposed_value=None,
    )
    rec = Recommendation(
        row=1,
        field="State",
        action="verify_state",
        current_value="XX",
        proposed_value=None,
        confidence=1.0,
        reasoning="State 'XX' in row 1 is unrecognized.",
    )

    state.quality_issues.append(med_issue)
    state.recommendations.append(rec)

    pending = service.get_pending_review_items(state)
    assert len(pending["quality_issues"]) == 1
    assert pending["quality_issues"][0].severity == "medium"
    assert pending["quality_issues"][0].field == "State"
    assert pending["quality_issues"][0].requires_human_review is True
    assert len(pending["recommendations"]) == 1
    assert pending["recommendations"][0].field == "State"


def test_high_issue_in_human_review():
    """HIGH issue -> appears in human-review inbox."""
    service = HumanReviewService()
    state = _create_sample_state("job-high-test")

    high_issue = QualityIssue(
        row=1,
        field="Reference",
        issue="Mandatory field 'Reference' is empty or whitespace.",
        severity=IssueSeverity.high.value,
        current_value=None,
        recommendation="Provide the original property identifier.",
        reasoning="Reference is missing in row 1.",
        issue_type=IssueType.missing_value.value,
        requires_human_review=True,
        reasoning_source="deterministic",
        qwen_used=False,
        proposed_value=None,
    )
    rec = Recommendation(
        row=1,
        field="Reference",
        action="supply_reference",
        current_value=None,
        proposed_value=None,
        confidence=1.0,
        reasoning="Reference is missing in row 1.",
    )

    state.quality_issues.append(high_issue)
    state.recommendations.append(rec)

    pending = service.get_pending_review_items(state)
    assert len(pending["quality_issues"]) == 1
    assert pending["quality_issues"][0].severity == "high"
    assert pending["quality_issues"][0].field == "Reference"
    assert pending["quality_issues"][0].requires_human_review is True
    assert len(pending["recommendations"]) == 1
    assert pending["recommendations"][0].field == "Reference"


def test_dataset_with_low_and_medium_returns_only_medium_in_review_queue():
    """Dataset containing LOW + MEDIUM issues returns only the MEDIUM issue in pending review queue."""
    service = HumanReviewService()
    state = _create_sample_state("job-low-med-test")

    low_issue = QualityIssue(
        row=1,
        field="County",
        issue="Field 'County' is empty.",
        severity=IssueSeverity.low.value,
        current_value=None,
        recommendation="Provide County from source records if available.",
        reasoning="County is missing in row 1.",
        issue_type=IssueType.missing_value.value,
        requires_human_review=False,
        reasoning_source="deterministic",
        qwen_used=False,
        proposed_value=None,
    )
    med_issue = QualityIssue(
        row=2,
        field="State",
        issue="'XX' is not a recognized state code.",
        severity=IssueSeverity.medium.value,
        current_value="XX",
        recommendation="Confirm state code.",
        reasoning="State 'XX' in row 2 is unrecognized.",
        issue_type=IssueType.inconsistent_value.value,
        requires_human_review=True,
        reasoning_source="deterministic",
        qwen_used=False,
        proposed_value=None,
    )

    rec_low = Recommendation(
        row=1,
        field="County",
        action="supply_county",
        current_value=None,
        proposed_value=None,
        confidence=1.0,
        reasoning="County is missing.",
    )
    rec_med = Recommendation(
        row=2,
        field="State",
        action="verify_state",
        current_value="XX",
        proposed_value=None,
        confidence=1.0,
        reasoning="State is unrecognized.",
    )

    state.quality_issues.extend([low_issue, med_issue])
    state.recommendations.extend([rec_low, rec_med])

    # In audit state, both issues exist
    assert len(state.quality_issues) == 2

    # In review inbox, only MEDIUM issue is returned
    pending = service.get_pending_review_items(state)
    assert len(pending["quality_issues"]) == 1
    assert pending["quality_issues"][0].field == "State"
    assert pending["quality_issues"][0].severity == "medium"
    assert pending["quality_issues"][0].requires_human_review is True

    # In review recommendations, only matching MEDIUM recommendation is returned
    assert len(pending["recommendations"]) == 1
    assert pending["recommendations"][0].field == "State"
    assert pending["recommendations"][0].row == 2


def test_clean_dataset_produces_no_human_review_items():
    """A clean dataset produces no human-review items."""
    service = HumanReviewService()
    state = _create_sample_state("job-clean-test")

    # Clean state has empty issues and recommendations
    state.quality_issues = []
    state.recommendations = []

    pending = service.get_pending_review_items(state)
    assert len(pending["quality_issues"]) == 0
    assert len(pending["recommendations"]) == 0


def test_orchestrator_pipeline_end_to_end_routing():
    """End-to-end pipeline test showing Agent 3 generates LOW and MEDIUM issues,
    audit records both, and human review inbox displays only the MEDIUM issue."""
    orchestrator = PipelineOrchestrator()

    state = orchestrator.create_job(
        filename="test_policy_routing.xlsx",
        file_path="data/uploads/test_policy_routing.xlsx",
        file_size_bytes=2048,
    )
    job_id = state.job_id

    # Row 1 has missing County (LOW issue: requires_human_review = False)
    row_low = dict(_CLEAN_ROW)
    row_low["County"] = None

    # Row 2 has unrecognized State (MEDIUM issue: requires_human_review = True)
    row_med = dict(_CLEAN_ROW)
    row_med["Reference"] = "LOC-002"
    row_med["State"] = "INVALID"

    orchestrator._jobs[job_id].metadata["mapped_rows"] = [row_low, row_med]
    orchestrator._jobs[job_id].metadata["raw_columns"] = list(_CLEAN_ROW.keys())

    # Run analysis pipeline (Agent 1 -> Agent 2 -> Agent 3)
    state = orchestrator.run_analysis_pipeline(job_id)
    assert state.status == JobStatus.AWAITING_REVIEW

    # Audit retains all detected issues
    severities = {issue.severity for issue in state.quality_issues}
    assert "low" in severities
    assert "medium" in severities

    # Low issue appears in audit info
    low_issues = [i for i in state.quality_issues if i.severity == "low"]
    assert len(low_issues) == 1
    assert low_issues[0].requires_human_review is False

    # Pending human review inbox contains ONLY the medium issue
    pending = orchestrator.review_service.get_pending_review_items(state)
    assert len(pending["quality_issues"]) == 1
    assert pending["quality_issues"][0].severity == "medium"
    assert pending["quality_issues"][0].field == "State"
    assert pending["quality_issues"][0].requires_human_review is True

    # Pending recommendations contain only the medium recommendation
    assert len(pending["recommendations"]) == 1
    assert pending["recommendations"][0].field == "State"
