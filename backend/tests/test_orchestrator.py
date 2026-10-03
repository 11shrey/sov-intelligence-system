"""Test Pipeline Orchestrator flow."""

from app.orchestration.orchestrator import PipelineOrchestrator
from app.orchestration.state import JobStatus
from app.models.review_models import ReviewDecision, ReviewSubmission


_SAMPLE_COLUMNS = [
    "Loc #", "Street Address", "City", "ST", "Zip Code",
    "County", "Country", "Bldg Repl Cost", "Contents", "BI Limit",
    "Occupancy Type", "Const Type", "Stories", "Building Count",
    "Yr Built", "Fire Prot.", "Other Value",
]

_SAMPLE_MAPPED_ROWS = [
    {
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
    },
    # Duplicate record so Agent 3 generates at least one quality issue
    {
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
    },
]


def test_orchestrator_complete_lifecycle():
    """Verify orchestrator coordinates the complete lifecycle end-to-end."""
    orchestrator = PipelineOrchestrator()

    # 1. Job Creation
    state = orchestrator.create_job(
        filename="broker_submission.xlsx",
        file_path="data/uploads/broker_submission.xlsx",
        file_size_bytes=5000,
    )
    job_id = state.job_id
    assert orchestrator.get_job_state(job_id) is not None
    assert state.status == JobStatus.PENDING

    # Inject real source data into state metadata so Agent 2 & 3 can run fully.
    # (Agent 1 is still a placeholder that doesn't read a real file.)
    orchestrator._jobs[job_id].metadata["raw_columns"] = _SAMPLE_COLUMNS
    orchestrator._jobs[job_id].metadata["mapped_rows"] = _SAMPLE_MAPPED_ROWS

    # 2. Run Phase A Pipeline (Agent 1 -> Agent 2 -> Agent 3)
    state = orchestrator.run_analysis_pipeline(job_id)
    assert state.status == JobStatus.AWAITING_REVIEW
    assert len(state.sheet_analysis) > 0
    assert len(state.schema_mappings) > 0
    # At least one quality issue from the duplicate row
    assert len(state.quality_issues) > 0

    # 3. Apply Human Review — use first quality issue as the action target
    first_issue = state.quality_issues[0]
    submission = ReviewSubmission(
        decisions=[
            ReviewDecision(
                row=first_issue.row,
                field=first_issue.field,
                decision="approve",
                reviewer="senior_underwriter",
            )
        ]
    )
    state = orchestrator.apply_human_review(job_id, submission)
    assert state.status == JobStatus.REVIEW_COMPLETED
    assert len(state.review_decisions) == 1

    # 4. Run Phase B Pipeline (Agent 4 Controlled Transformation)
    state = orchestrator.run_transformation_pipeline(job_id)
    assert state.status == JobStatus.COMPLETED
    assert len(state.approved_transformations) == 1
    assert state.final_output_path is not None

    # 5. Audit Trail Verification
    audit_report = orchestrator.audit_service.get_audit_trail(state)
    assert audit_report.total_entries >= 4
