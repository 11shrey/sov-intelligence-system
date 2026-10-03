"""Pipeline Orchestrator

Coordinates the sequential lifecycle execution across all four agents, human review gates,
and audit logging.

Intended Flow:
  Upload
    ↓
  Agent 1: Sheet Intelligence
    ↓
  Agent 2: Schema Mapping
    ↓
  Agent 3: Data Quality & Reasoning
    ↓
  Human Review Gate (Approve / Reject / Edit)
    ↓
  Agent 4: Controlled Transformation
    ↓
  Audit Log Recording
    ↓
  Cleaned Standardized SOV Export
"""

from typing import Any
import uuid

from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus
from app.agents.sheet_agent import SheetIntelligenceAgent
from app.agents.schema_agent import SchemaMappingAgent
from app.agents.quality_agent import DataQualityAgent
from app.agents.transformation_agent import ControlledTransformationAgent
from app.review.human_review import HumanReviewService
from app.audit.audit_service import AuditService
from app.models.review_models import ReviewSubmission


class PipelineOrchestrator:
    """
    Central orchestrator coordinating state flow across all agents and services.
    """

    def __init__(self):
        self.sheet_agent = SheetIntelligenceAgent()
        self.schema_agent = SchemaMappingAgent()
        self.quality_agent = DataQualityAgent()
        self.transformation_agent = ControlledTransformationAgent()
        self.review_service = HumanReviewService()
        self.audit_service = AuditService()

        # In-memory storage for active job states (Supabase integration in Phase 3)
        self._jobs: dict[str, SOVProcessingState] = {}

    def create_job(
        self,
        filename: str,
        file_path: str,
        file_size_bytes: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> SOVProcessingState:
        """
        Initialize a new SOV processing job with FileInfo.
        """
        job_id = str(uuid.uuid4())
        file_info = FileInfo(
            filename=filename,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
        )
        state = SOVProcessingState(
            job_id=job_id,
            file_info=file_info,
            status=JobStatus.PENDING,
            metadata=metadata or {},
        )
        self._jobs[job_id] = state

        # Log job creation audit event
        self.audit_service.log_event(
            state=state,
            user_id="system",
            action="job_created",
            source=filename,
            target="pipeline",
            before=None,
            after={"status": "pending"},
        )
        return state

    def get_job_state(self, job_id: str) -> SOVProcessingState | None:
        """
        Retrieve the current in-memory state for a given job ID.
        """
        return self._jobs.get(job_id)

    def run_analysis_pipeline(self, job_id: str) -> SOVProcessingState:
        """
        Execute Phase A of the pipeline: Agent 1 -> Agent 2 -> Agent 3.
        Brings state to AWAITING_REVIEW status.
        """
        state = self._jobs.get(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")

        # Step 1: Sheet Intelligence (Agent 1)
        state = self.sheet_agent.run(state)
        self.audit_service.log_event(
            state=state,
            user_id="agent_1_sheet_intelligence",
            action="sheet_analysis_completed",
            source=state.file_info.filename,
            target=state.selected_sheet or "none",
            before=None,
            after={"selected_sheet": state.selected_sheet, "header_row": state.header_row},
        )

        # Step 2: Schema Mapping (Agent 2)
        state = self.schema_agent.run(state)
        self.audit_service.log_event(
            state=state,
            user_id="agent_2_schema_mapping",
            action="schema_mapping_completed",
            source=state.selected_sheet or "sheet",
            target="target_sov_schema",
            before=None,
            after={"mapped_columns_count": len(state.schema_mappings)},
        )

        # Step 3: Data Quality & Reasoning (Agent 3)
        state = self.quality_agent.run(state)
        self.audit_service.log_event(
            state=state,
            user_id="agent_3_data_quality",
            action="quality_inspection_completed",
            source="mapped_dataset",
            target="recommendations",
            before=None,
            after={
                "issues_count": len(state.quality_issues),
                "recommendations_count": len(state.recommendations),
            },
        )

        # State is now in AWAITING_REVIEW
        return state

    def apply_human_review(
        self, job_id: str, submission: ReviewSubmission
    ) -> SOVProcessingState:
        """
        Apply human decisions (approve / reject / edit) to the job recommendations.
        """
        state = self._jobs.get(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")

        state = self.review_service.record_decisions(state, submission)

        # Log human review audit event
        for decision in submission.decisions:
            self.audit_service.log_event(
                state=state,
                user_id=decision.reviewer,
                action=f"review_decision_{decision.decision}",
                source=f"Row {decision.row}, {decision.field}",
                target=decision.field,
                before=None,
                after=decision.edited_value if decision.decision == "edit" else decision.decision,
                approver=decision.reviewer,
            )

        return state

    def run_transformation_pipeline(self, job_id: str) -> SOVProcessingState:
        """
        Execute Phase B of the pipeline: Agent 4 (Controlled Transformation)
        Produces clean SOV output.
        """
        state = self._jobs.get(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")

        # Step 4: Controlled Transformation (Agent 4)
        state = self.transformation_agent.run(state)

        # Final audit logging
        self.audit_service.log_event(
            state=state,
            user_id="agent_4_transformation",
            action="transformations_applied",
            source="approved_decisions",
            target=state.final_output_path or "cleaned_sov.xlsx",
            before=None,
            after={"total_transformations": len(state.approved_transformations)},
        )

        return state
