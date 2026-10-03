"""Test Pipeline Orchestrator flow."""

from pathlib import Path
from openpyxl import Workbook
import pytest

from app.orchestration.orchestrator import PipelineOrchestrator
from app.orchestration.state import JobStatus
from app.models.review_models import ReviewDecision, ReviewSubmission


def test_orchestrator_complete_lifecycle(tmp_path: Path):
    """Verify orchestrator coordinates the complete lifecycle end-to-end."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Locations"
    ws.append(["Reference", "Address", "City", "State", "Zip", "Building Value"])
    ws.append(["LOC-01", "500 Main St", "Houston", "TX", "77002", 2500000])

    wb_path = tmp_path / "broker_submission.xlsx"
    wb.save(wb_path)

    orchestrator = PipelineOrchestrator()

    # 1. Job Creation
    state = orchestrator.create_job(
        filename=wb_path.name,
        file_path=str(wb_path),
        file_size_bytes=5000,
    )
    job_id = state.job_id
    assert orchestrator.get_job_state(job_id) is not None
    assert state.status == JobStatus.PENDING

    # 2. Run Phase A Pipeline (Agent 1 -> Agent 2 -> Agent 3)
    state = orchestrator.run_analysis_pipeline(job_id)
    assert state.status == JobStatus.AWAITING_REVIEW
    assert len(state.sheet_analysis) > 0
    assert len(state.schema_mappings) > 0
    assert len(state.recommendations) > 0

    # 3. Apply Human Review
    submission = ReviewSubmission(
        decisions=[
            ReviewDecision(
                row=state.recommendations[0].row,
                field=state.recommendations[0].field,
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
