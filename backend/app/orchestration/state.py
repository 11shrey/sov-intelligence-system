from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from app.models.sheet_models import SheetAnalysis
from app.models.schema_models import SchemaMapping
from app.models.quality_models import QualityIssue, Recommendation
from app.models.review_models import ReviewDecision
from app.models.transformation_models import Transformation
from app.models.audit_models import AuditEntry


class JobStatus(str, Enum):
    """Lifecycle status for an SOV processing job."""

    PENDING = "pending"
    SHEET_ANALYZED = "sheet_analyzed"
    SCHEMA_MAPPED = "schema_mapped"
    QUALITY_CHECKED = "quality_checked"
    AWAITING_REVIEW = "awaiting_review"
    REVIEW_COMPLETED = "review_completed"
    TRANSFORMING = "transforming"
    COMPLETED = "completed"
    FAILED = "failed"


class FileInfo(BaseModel):
    """Metadata describing the uploaded SOV file."""

    filename: str = Field(..., description="Original name of the uploaded file")
    file_path: str = Field(..., description="Local or remote path where the file is stored")
    file_size_bytes: int = Field(default=0, description="Size of the file in bytes")
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of upload",
    )


class SOVProcessingState(BaseModel):
    """
    Unified shared state container passed sequentially through the multi-agent pipeline.

    Flow:
      Upload -> Agent 1 (Sheet Intelligence)
             -> Agent 2 (Schema Mapping)
             -> Agent 3 (Data Quality)
             -> Human Review
             -> Agent 4 (Controlled Transformation)
             -> Audit & Export
    """

    job_id: str = Field(..., description="Unique job execution identifier (UUID)")
    file_info: FileInfo = Field(..., description="Metadata of the raw input file")
    status: JobStatus = Field(
        default=JobStatus.PENDING, description="Current stage in the pipeline lifecycle"
    )

    # -------------------------------------------------------------
    # Agent 1: Sheet Intelligence Outputs
    # -------------------------------------------------------------
    sheet_analysis: list[SheetAnalysis] = Field(
        default_factory=list,
        description="Evaluated candidate SOV tabs across workbook sheets",
    )
    selected_sheet: str | None = Field(
        default=None,
        description="The primary sheet selected for extraction",
    )
    header_row: int | None = Field(
        default=None,
        description="0-indexed or 1-indexed header row detected in the selected sheet",
    )

    # -------------------------------------------------------------
    # Agent 2: Schema Mapping Outputs
    # -------------------------------------------------------------
    schema_mappings: list[SchemaMapping] = Field(
        default_factory=list,
        description="Mappings from source sheet columns to the 17 standard SOV fields",
    )

    # -------------------------------------------------------------
    # Agent 3: Data Quality & Reasoning Outputs
    # -------------------------------------------------------------
    quality_issues: list[QualityIssue] = Field(
        default_factory=list,
        description="Quality defects and anomalies detected across records",
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Proposed automated fixes for human review",
    )

    # -------------------------------------------------------------
    # Human-in-the-Loop Review Decisions
    # -------------------------------------------------------------
    review_decisions: list[ReviewDecision] = Field(
        default_factory=list,
        description="Human decisions (approve / reject / edit) recorded for proposed fixes",
    )

    # -------------------------------------------------------------
    # Agent 4: Controlled Transformation Outputs
    # -------------------------------------------------------------
    approved_transformations: list[Transformation] = Field(
        default_factory=list,
        description="Log of mutations actually executed on the dataset",
    )
    final_output_path: str | None = Field(
        default=None,
        description="File path or URL to the generated, standardized clean SOV",
    )

    # -------------------------------------------------------------
    # Audit Trail & System Metadata
    # -------------------------------------------------------------
    audit_log: list[AuditEntry] = Field(
        default_factory=list,
        description="Immutable audit entries recording all agent and human interactions",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary workflow metadata, runtime metrics, or session attributes",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of warning or error messages encountered during processing",
    )
