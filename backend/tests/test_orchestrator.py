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


def test_orchestrator_m3_end_to_end_flow():
    """
    Verify complete M3 integration end-to-end:
    1. Recommendations enter Human Review
    2. Human Review handles ACCEPT, EDIT, REJECT, and PENDING
    3. Agent 4 respects decisions (only ACCEPT/EDIT applied)
    4. Accepted/edited transformations are reflected in output
    5. Rejected/pending values remain unchanged
    6. Audit records created appropriately (including reject before==after, no pending accepted)
    7. Cleaned_SOV.xlsx has exactly 17 canonical fields
    8. Original source data is not mutated
    """
    import copy
    from pathlib import Path
    import pandas as pd
    from app.models.quality_models import Recommendation
    from app.services.excel_service import STANDARD_FIELDS

    orchestrator = PipelineOrchestrator()
    state = orchestrator.create_job(
        filename="portfolio_m3.xlsx",
        file_path="data/uploads/portfolio_m3.xlsx",
        file_size_bytes=4096,
    )
    job_id = state.job_id

    # 1. Provide 4 recommendations to enter Human Review
    recs = [
        Recommendation(
            row=1,
            field="Building Value",
            action="format_currency",
            current_value="$1,250,000",
            proposed_value=1250000.0,
            confidence=0.98,
            reasoning="Normalized currency to float",
        ),
        Recommendation(
            row=2,
            field="Fire Sprinklers (Y/N)",
            action="standardize_sprinkler",
            current_value="YES",
            proposed_value="Y",
            confidence=0.95,
            reasoning="Converted YES to Y",
        ),
        Recommendation(
            row=3,
            field="Zip",
            action="fix_zip",
            current_value="02110",
            proposed_value="02110",
            confidence=0.85,
            reasoning="Valid zip code",
        ),
        Recommendation(
            row=4,
            field="City",
            action="standardize_city",
            current_value="Boston",
            proposed_value="Greater Boston",
            confidence=0.70,
            reasoning="Proposed broader metro name",
        ),
    ]
    state.recommendations = recs
    state.status = JobStatus.AWAITING_REVIEW

    # Snapshot to verify immutability later
    recs_snapshot = copy.deepcopy(recs)

    # 2. Human Review decisions:
    # Rec 1 -> ACCEPT ("approve")
    # Rec 2 -> EDIT ("edit", edited_value="N")
    # Rec 3 -> REJECT ("reject")
    # Rec 4 -> PENDING (no decision submitted)
    submission = ReviewSubmission(
        decisions=[
            ReviewDecision(
                row=1,
                field="Building Value",
                decision="approve",
                reviewer="lead_underwriter",
            ),
            ReviewDecision(
                row=2,
                field="Fire Sprinklers (Y/N)",
                decision="edit",
                edited_value="N",
                reviewer="lead_underwriter",
            ),
            ReviewDecision(
                row=3,
                field="Zip",
                decision="reject",
                reviewer="lead_underwriter",
            ),
        ]
    )

    state = orchestrator.apply_human_review(job_id, submission)
    assert state.status == JobStatus.REVIEW_COMPLETED
    assert len(state.review_decisions) == 3

    # 3. Agent 4 Controlled Transformation
    state = orchestrator.run_transformation_pipeline(job_id)
    assert state.status == JobStatus.COMPLETED

    # Agent 4 must only apply ACCEPT and EDIT (2 transformations)
    assert len(state.approved_transformations) == 2
    transformed_fields = {t.field: t.after for t in state.approved_transformations}
    assert transformed_fields["Building Value"] == 1250000.0
    assert transformed_fields["Fire Sprinklers (Y/N)"] == "N"
    assert "Zip" not in transformed_fields
    assert "City" not in transformed_fields

    # 4 & 5. Verify Cleaned_SOV.xlsx output content
    assert state.final_output_path is not None
    output_path = Path(state.final_output_path)
    assert output_path.exists()

    df = pd.read_excel(output_path, sheet_name="Cleaned SOV", dtype={"Zip": str, "Reference": str})

    # 7. Exactly 17 columns in exact order
    assert list(df.columns) == STANDARD_FIELDS
    assert len(df.columns) == 17

    # 4. Accepted/edited transformations reflected in output
    row1 = df[df["Reference"] == "LOC-001"].iloc[0]
    assert row1["Building Value"] == 1250000.0

    row2 = df[df["Reference"] == "LOC-002"].iloc[0]
    assert row2["Fire Sprinklers (Y/N)"] == "N"

    # 5. Rejected / pending values remain unchanged
    row3 = df[df["Reference"] == "LOC-003"].iloc[0]
    assert str(row3["Zip"]) == "02110"

    row4 = df[df["Reference"] == "LOC-004"].iloc[0]
    assert row4["City"] == "Boston"

    # 6. Audit trail verification
    audit_report = orchestrator.audit_service.get_audit_trail(state)
    actions = [e.action for e in audit_report.entries]
    assert "applied_transformation_approve" in actions
    assert "applied_transformation_edit" in actions
    assert "recommendation_rejected" in actions

    # Reject record has before == after
    reject_entry = next(e for e in audit_report.entries if e.action == "recommendation_rejected")
    assert reject_entry.before == reject_entry.after == "02110"

    # Pending recommendation has NO applied_transformation
    for entry in audit_report.entries:
        if "applied_transformation" in entry.action:
            assert entry.target != "City"

    # 8. Source data not mutated
    assert state.recommendations == recs_snapshot
