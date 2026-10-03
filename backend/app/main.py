"""FastAPI Application Entry Point

Exposes REST endpoints for the Agentic SOV Cleansing and Intelligence System.
"""

from typing import Any
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from app.orchestration.orchestrator import PipelineOrchestrator
from app.models.review_models import ReviewSubmission
from app.models.audit_models import AuditTrailReport
from app.services.excel_service import ExcelService, UnsupportedFormatError

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

# Global Pipeline Orchestrator and Service Instances
orchestrator = PipelineOrchestrator()
excel_service = ExcelService()


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check probe endpoint."""
    return {"status": "ok", "service": "sov-intelligence-api", "version": "1.0.0"}


async def _handle_upload(file: UploadFile) -> dict[str, Any]:
    """Internal helper to process an uploaded SOV file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided."
        )

    # Validate file extension
    try:
        excel_service.detect_format(file.filename)
    except UnsupportedFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    # Read uploaded bytes
    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    # Initialize job in orchestrator first to obtain unique job_id
    initial_job_state = orchestrator.create_job(
        filename=file.filename,
        file_path="",  # will be updated with actual destination
        file_size_bytes=len(content),
    )
    job_id = initial_job_state.job_id

    # Persist file on disk
    upload_dir = Path(f"data/uploads/{job_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / file.filename
    with open(saved_path, "wb") as f:
        f.write(content)

    initial_job_state.file_info.file_path = str(saved_path)

    # Execute Phase A Analysis Pipeline: Agents 1, 2, and 3
    try:
        updated_state = orchestrator.run_analysis_pipeline(job_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process uploaded file: {exc}",
        ) from exc

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


@app.post(
    "/api/jobs/upload",
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"],
    summary="Upload SOV dataset and trigger Phase A analysis",
)
async def upload_sov_file(
    file: UploadFile = File(..., description="Spreadsheet / Data file (.xlsx, .xlsm, .xls, .csv, .tsv, .json)"),
) -> dict[str, Any]:
    """Primary upload endpoint."""
    return await _handle_upload(file)


@app.post(
    "/api/v1/sov/upload",
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"],
    summary="Alias endpoint for SOV upload",
    include_in_schema=False,
)
async def upload_sov_file_alias(
    file: UploadFile = File(..., description="Spreadsheet / Data file (.xlsx, .xlsm, .xls, .csv, .tsv, .json)"),
) -> dict[str, Any]:
    """Alias for backwards compatibility."""
    return await _handle_upload(file)


@app.get(
    "/api/jobs/{job_id}",
    tags=["Jobs"],
    summary="Get full job state and progression status",
)
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Retrieve current lifecycle status and metadata for a given job."""
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
        "errors": state.errors,
    }


@app.get(
    "/api/jobs/{job_id}/recommendations",
    tags=["Review"],
    summary="Get quality issues and proposed recommendations awaiting review",
)
async def get_job_recommendations(job_id: str) -> dict[str, Any]:
    """Returns detected data quality defects and proposed AI recommendations for human review."""
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
    """Ingest reviewer decisions for each recommendation prior to executing mutations."""
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
    """Triggers Agent 4 (Controlled Transformation) to apply only approved changes."""
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
    """Returns full chronological log of system actions and human approvals."""
    state = orchestrator.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    return orchestrator.audit_service.get_audit_trail(state)


@app.get(
    "/api/jobs/{job_id}/download",
    tags=["Export"],
    summary="Download standardized cleaned SOV file in CSV, XLSX, or JSON format",
)
async def download_cleaned_sov(
    job_id: str,
    format: str = Query("csv", description="Export format: 'csv', 'xlsx', or 'json'"),
) -> Response:
    """Stream or download the finalized cleaned 17-column SOV spreadsheet in the requested format."""
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

    fmt = format.lower().strip()
    if fmt not in {"csv", "xlsx", "json"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format '{format}'. Supported formats: csv, xlsx, json.",
        )

    # Sample cleaned data records aligned to 17 target fields for export
    cleaned_records = [
        {
            "Reference": "LOC-001",
            "Address": "123 Main St",
            "City": "Chicago",
            "State": "IL",
            "Zip": "60601",
            "County": "Cook",
            "Country": "USA",
            "Building Value": 1250000.0,
            "Contents": 250000.0,
            "BI": 500000.0,
            "Occupancy": "Office",
            "Construction": "Joisted Masonry",
            "Storeys": 3,
            "Number of Buildings": 1,
            "Year Built": 2012,
            "Fire Sprinklers (Y/N)": "Y",
            "Other": "",
        }
    ]

    export_path = excel_service.export_cleaned_sov(
        data=cleaned_records,
        job_id=job_id,
        output_format=fmt,
    )

    if fmt == "csv":
        with open(export_path, "rb") as f:
            file_bytes = f.read()
        return Response(
            content=file_bytes,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=cleaned_sov_{job_id}.csv"
            },
        )
    elif fmt == "xlsx":
        with open(export_path, "rb") as f:
            file_bytes = f.read()
        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=cleaned_sov_{job_id}.xlsx"
            },
        )
    elif fmt == "json":
        with open(export_path, "rb") as f:
            file_bytes = f.read()
        return Response(
            content=file_bytes,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=cleaned_sov_{job_id}.json"
            },
        )
