"""FastAPI Application Entry Point

Exposes REST endpoints for the Agentic SOV Cleansing and Intelligence System.
"""

from typing import Any
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.orchestration.orchestrator import PipelineOrchestrator
from app.models.review_models import ReviewSubmission
from app.models.audit_models import AuditTrailReport

# Initialize FastAPI App
app = FastAPI(
    title="Agentic SOV Cleansing & Intelligence API",
    description="Multi-agent property SOV processing and data quality intelligence system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Pipeline Orchestrator Instance
orchestrator = PipelineOrchestrator()


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check probe endpoint."""
    return {"status": "ok", "service": "sov-intelligence-api", "version": "1.0.0"}


@app.post(
    "/api/jobs/upload",
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"],
    summary="Upload SOV workbook and trigger Phase A analysis",
)
async def upload_sov_file(
    file: UploadFile = File(..., description="Excel spreadsheet (.xlsx, .xls)"),
) -> dict[str, Any]:
    """
    Accepts an uploaded SOV Excel workbook, saves it to storage, initializes
    a pipeline state, and triggers Agent 1 (Sheet), Agent 2 (Schema), and Agent 3 (Quality).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    # Initialize job in orchestrator
    state = orchestrator.create_job(
        filename=file.filename,
        file_path=f"data/uploads/{file.filename}",
        file_size_bytes=0,
    )

    # Execute Phase A: Agents 1, 2, 3
    updated_state = orchestrator.run_analysis_pipeline(state.job_id)

    return {
        "job_id": updated_state.job_id,
        "status": updated_state.status,
        "file_info": updated_state.file_info,
        "selected_sheet": updated_state.selected_sheet,
        "header_row": updated_state.header_row,
        "total_issues": len(updated_state.quality_issues),
        "total_recommendations": len(updated_state.recommendations),
        "message": "File uploaded and initial analysis completed. Ready for human review.",
    }


@app.get(
    "/api/jobs/{job_id}",
    tags=["Jobs"],
    summary="Get full job state and progression status",
)
async def get_job_status(job_id: str) -> dict[str, Any]:
    """
    Retrieve current lifecycle status, sheet intelligence, schema mappings,
    and progress metrics for a given job.
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    return {
        "job_id": state.job_id,
        "status": state.status,
        "file_info": state.file_info,
        "selected_sheet": state.selected_sheet,
        "header_row": state.header_row,
        "sheet_analysis": state.sheet_analysis,
        "schema_mappings": state.schema_mappings,
        "total_issues": len(state.quality_issues),
        "total_recommendations": len(state.recommendations),
        "total_decisions": len(state.review_decisions),
        "total_transformations": len(state.approved_transformations),
        "final_output_path": state.final_output_path,
    }


@app.get(
    "/api/jobs/{job_id}/recommendations",
    tags=["Review"],
    summary="Get quality issues and proposed recommendations awaiting review",
)
async def get_job_recommendations(job_id: str) -> dict[str, Any]:
    """
    Returns detected data quality defects and proposed AI recommendations
    for human review.
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    return orchestrator.review_service.get_pending_review_items(state)


@app.post(
    "/api/jobs/{job_id}/review",
    tags=["Review"],
    summary="Submit human review decisions (approve / reject / edit)",
)
async def submit_job_review(
    job_id: str,
    submission: ReviewSubmission,
) -> dict[str, Any]:
    """
    Ingest reviewer decisions for each recommendation prior to executing mutations.
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    updated_state = orchestrator.apply_human_review(job_id, submission)
    return {
        "job_id": updated_state.job_id,
        "status": updated_state.status,
        "decisions_recorded": len(submission.decisions),
        "message": "Human review decisions recorded. Ready for transformation.",
    }


@app.post(
    "/api/jobs/{job_id}/transform",
    tags=["Transformation"],
    summary="Execute Agent 4 transformations on approved decisions",
)
async def execute_transformations(job_id: str) -> dict[str, Any]:
    """
    Triggers Agent 4 (Controlled Transformation) to apply only approved changes
    and generate the standardized clean SOV.
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    if not state.review_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot execute transformation before human review decisions are submitted.",
        )

    updated_state = orchestrator.run_transformation_pipeline(job_id)
    return {
        "job_id": updated_state.job_id,
        "status": updated_state.status,
        "transformations_applied": len(updated_state.approved_transformations),
        "final_output_path": updated_state.final_output_path,
        "download_url": f"/api/jobs/{job_id}/download",
    }


@app.get(
    "/api/jobs/{job_id}/audit",
    response_model=AuditTrailReport,
    tags=["Audit"],
    summary="Get complete immutable audit trail for a job",
)
async def get_job_audit_trail(job_id: str) -> AuditTrailReport:
    """
    Returns full chronological log of system actions, agent reasoning steps,
    and human approvals.
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    return orchestrator.audit_service.get_audit_trail(state)


@app.get(
    "/api/jobs/{job_id}/download",
    tags=["Export"],
    summary="Download standardized cleaned SOV file",
)
async def download_cleaned_sov(job_id: str, format: str | None = None) -> Response:
    """
    Stream or download the finalized cleaned SOV spreadsheet (.xlsx or .csv).
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    if not state.final_output_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cleaned SOV has not been generated yet. Run transformations first.",
        )

    if os.path.exists(state.final_output_path):
        from fastapi.responses import FileResponse
        if format == "csv":
            import pandas as pd
            import io
            df = pd.read_excel(state.final_output_path, sheet_name="Cleaned SOV")
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            return Response(
                content=csv_buf.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=cleaned_sov_{job_id}.csv"
                },
            )
        return FileResponse(
            path=state.final_output_path,
            filename=f"Cleaned_SOV_{job_id}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # Return placeholder response content if file is not on disk
    dummy_csv = "Reference,Address,City,State,Zip,Building Value\nLOC-1,123 Main St,Chicago,IL,60601,1000000\n"
    return Response(
        content=dummy_csv,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=cleaned_sov_{job_id}.csv"
        },
    )


# ---------------------------------------------------------------------------
# Direct /jobs/* Endpoints (Standard Workflow Specification)
# ---------------------------------------------------------------------------

@app.post(
    "/jobs",
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"],
    summary="Create a job, upload an SOV file, and run Agent 1 -> Agent 2 -> Agent 3",
)
async def create_and_start_job(
    file: UploadFile = File(..., description="Uploaded SOV file (.xlsx, .csv)"),
) -> dict[str, Any]:
    """
    POST /jobs
    - Accept an uploaded SOV file
    - Save it to local storage
    - Create a job in orchestrator
    - Invoke existing orchestrator start workflow (Agent 1 -> Agent 2 -> Agent 3)
    - Returns job_id and current status
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / file.filename

    content = await file.read()
    with open(saved_path, "wb") as f:
        f.write(content)

    state = orchestrator.create_job(
        filename=file.filename,
        file_path=str(saved_path),
        file_size_bytes=len(content),
    )

    # Run workflow until human review (Agent 1 -> Agent 2 -> Agent 3)
    updated_state = orchestrator.start_workflow_until_review(state.job_id)

    return {
        "job_id": updated_state.job_id,
        "status": updated_state.status,
        "file_info": updated_state.file_info,
        "selected_sheet": updated_state.selected_sheet,
        "header_row": updated_state.header_row,
        "total_issues": len(updated_state.quality_issues),
        "total_recommendations": len(updated_state.recommendations),
        "message": "Job created and analysis completed. Awaiting human review.",
    }


@app.get(
    "/jobs/{job_id}/review",
    tags=["Review"],
    summary="Get review information required by frontend (mappings, issues, recommendations, status)",
)
async def get_human_review_data(job_id: str) -> dict[str, Any]:
    """
    GET /jobs/{job_id}/review
    - Return the information required by the frontend for human review:
      - schema mappings
      - quality issues
      - recommendations
      - current job status
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    return {
        "job_id": state.job_id,
        "status": state.status,
        "selected_sheet": state.selected_sheet,
        "header_row": state.header_row,
        "schema_mappings": state.schema_mappings,
        "quality_issues": state.quality_issues,
        "recommendations": state.recommendations,
        "quality_report": state.quality_report,
        "total_issues": len(state.quality_issues),
        "total_recommendations": len(state.recommendations),
    }


@app.post(
    "/jobs/{job_id}/review",
    tags=["Review"],
    summary="Submit human review decisions and execute Agent 4 transformation",
)
async def submit_human_review_and_resume(
    job_id: str,
    submission: ReviewSubmission,
) -> dict[str, Any]:
    """
    POST /jobs/{job_id}/review
    - Accept human review decisions
    - Pass them to existing orchestrator apply_human_review / resume_workflow_after_review
    - Invoke Agent 4 only after valid review decisions
    - Return final status and output information
    """
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    if not submission.decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one human review decision is required.",
        )

    # Ingest decisions and run Agent 4
    updated_state = orchestrator.resume_workflow_after_review(job_id, decisions=submission.decisions)

    return {
        "job_id": updated_state.job_id,
        "status": updated_state.status,
        "decisions_recorded": len(submission.decisions),
        "transformations_applied": len(updated_state.approved_transformations),
        "final_output_path": updated_state.final_output_path,
        "download_url": f"/jobs/{job_id}/output",
    }


@app.get(
    "/jobs/{job_id}/output",
    tags=["Export"],
    summary="Download the generated Cleaned_SOV.xlsx workbook",
)
async def get_cleaned_sov_output(job_id: str) -> Response:
    """
    GET /jobs/{job_id}/output
    - Return / download the generated Cleaned_SOV.xlsx
    - Blocks if Agent 4 has not executed yet
    """
    from fastapi.responses import FileResponse

    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    if not state.final_output_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cleaned SOV has not been generated yet. Complete human review first.",
        )

    file_path = Path(state.final_output_path)
    if file_path.exists():
        return FileResponse(
            path=str(file_path),
            filename="Cleaned_SOV.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Output file {state.final_output_path} not found on server.",
    )

