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

from typing import Any, List
import uuid
from pathlib import Path
import pandas as pd

import logging
from app.orchestration.state import SOVProcessingState, SOVState, FileInfo, JobStatus, SheetAnalysis
from app.agents.sheet_agent import SheetIntelligenceAgent
from app.agents.schema_agent import SchemaMappingAgent, LLMAdapter
logger = logging.getLogger(__name__)
from app.agents.quality_agent import DataQualityAgent
from app.agents.transformation_agent import ControlledTransformationAgent
from app.review.human_review import HumanReviewService
from app.audit.audit_service import AuditService
from app.models.review_models import ReviewDecision, ReviewSubmission
from app.services.excel_service import ExcelOutputService, STANDARD_FIELDS


class PipelineOrchestrator:
    """
    Central orchestrator coordinating state flow across all agents and services.
    """

    def __init__(self):
        self.sheet_agent = SheetIntelligenceAgent()
        self.schema_agent = SchemaMappingAgent(llm_adapter=LLMAdapter())
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
        Stops before Agent 4 (Human Review Pause).
        """
        state = self._jobs.get(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")

        # Step 1: Sheet Intelligence (Agent 1)
        file_path_str = state.file_info.file_path if state.file_info else ""
        if file_path_str and Path(file_path_str).exists():
            try:
                from app.agents.sheet_intelligence import analyze_file
                handoff = analyze_file(file_path_str, job_id=state.job_id)
                state.selected_sheet = handoff.selected_sheet
                state.header_row = handoff.header_row
                state.status = JobStatus.SHEET_ANALYZED
                if handoff.raw_headers and "raw_columns" not in state.metadata:
                    state.metadata["raw_columns"] = handoff.raw_headers
                # Populate sheet_analysis summary
                state.sheet_analysis = [
                    SheetAnalysis(
                        sheet_name=a.sheet_name,
                        is_candidate=a.is_candidate,
                        header_row=a.header_row,
                        confidence=a.confidence,
                        reasoning="; ".join(a.reasoning) if isinstance(a.reasoning, list) else str(a.reasoning),
                    )
                    for a in handoff.all_sheets_evaluated
                ]
            except Exception as e:
                logger.warning("Agent 1 analysis_file failed: %s. Falling back to sheet_agent.run()", e)
                state = self.sheet_agent.run(state)
        else:
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

        # Thin Adapter: Extract raw headers from file if not already provided in metadata
        self._adapt_agent1_to_agent2(state)

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

        # Thin Adapter: Map raw rows into canonical-keyed records for Agent 3 if not present
        self._adapt_agent2_to_agent3(state)

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

        # State is now in AWAITING_REVIEW — Human Review Pause
        state.status = JobStatus.AWAITING_REVIEW
        return state

    # Alias method matching requirements
    def start_workflow_until_review(self, job_id: str) -> SOVProcessingState:
        """Run workflow from upload up until human review pause."""
        return self.run_analysis_pipeline(job_id)

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

        if state.status != JobStatus.REVIEW_COMPLETED and not state.review_decisions:
            raise ValueError("Human review decisions are required before running Agent 4 transformation.")

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

    # Alias method matching requirements
    def resume_workflow_after_review(
        self, job_id: str, decisions: list[ReviewDecision] | None = None
    ) -> SOVProcessingState:
        """Resume workflow after human review decisions by executing Agent 4."""
        state = self._jobs.get(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")

        if decisions:
            self.apply_human_review(job_id, ReviewSubmission(decisions=decisions))

        return self.run_transformation_pipeline(job_id)

    # ------------------------------------------------------------------
    # Thin Adapters connecting Agent 1, Agent 2, Agent 3 data contracts
    # ------------------------------------------------------------------
    def _adapt_agent1_to_agent2(self, state: SOVProcessingState) -> None:
        """Ensure state.metadata['raw_columns'] is populated for Agent 2."""
        if "raw_columns" in state.metadata and state.metadata["raw_columns"]:
            return

        file_path_str = state.file_info.file_path if state.file_info else ""
        if not file_path_str:
            return

        path = Path(file_path_str)
        if not path.exists():
            return

        try:
            sheet_name = state.selected_sheet or 0
            header_row = state.header_row if state.header_row is not None else 0

            if path.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
                df_headers = pd.read_excel(path, sheet_name=sheet_name, header=header_row, nrows=1)
                raw_cols = [str(c).strip() for c in df_headers.columns if str(c).strip()]
                state.metadata["raw_columns"] = raw_cols
            elif path.suffix.lower() == ".csv":
                df_headers = pd.read_csv(path, header=header_row, nrows=1)
                raw_cols = [str(c).strip() for c in df_headers.columns if str(c).strip()]
                state.metadata["raw_columns"] = raw_cols
        except Exception:
            pass

    def _adapt_agent2_to_agent3(self, state: SOVProcessingState) -> None:
        """Map raw file data rows into canonical schema rows for Agent 3."""
        if "mapped_rows" in state.metadata and state.metadata["mapped_rows"]:
            return

        file_path_str = state.file_info.file_path if state.file_info else ""
        if not file_path_str or not state.schema_mappings:
            return

        path = Path(file_path_str)
        if not path.exists():
            return

        try:
            sheet_name = state.selected_sheet or 0
            header_row = state.header_row if state.header_row is not None else 0

            if path.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
                df_data = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
            elif path.suffix.lower() == ".csv":
                df_data = pd.read_csv(path, header=header_row)
            else:
                return

            col_to_target = {
                m.source_column: m.target_field
                for m in state.schema_mappings
                if m.target_field and m.target_field != "unmapped"
            }

            mapped_rows: list[dict[str, Any]] = []
            for _, row in df_data.iterrows():
                row_dict: dict[str, Any] = {}
                for col in df_data.columns:
                    target_field = col_to_target.get(str(col).strip())
                    if target_field:
                        row_dict[target_field] = row[col]
                mapped_rows.append(row_dict)

            state.metadata["mapped_rows"] = mapped_rows
            if "source_rows" not in state.metadata:
                state.metadata["source_rows"] = mapped_rows
        except Exception:
            pass
