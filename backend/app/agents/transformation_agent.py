"""Agent 4: Controlled Transformation Agent

Responsible for:
- Reading approved human review decisions from state.review_decisions.
- Applying data transformations deterministically (applying approved values or human edits).
- Generating transformation log entries (Transformation) and audit records (AuditEntry).
- Producing the final cleaned SOV output dataset.
"""

from datetime import datetime, timezone
from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.transformation_models import Transformation
from app.models.audit_models import AuditEntry


class ControlledTransformationAgent:
    """
    Agent 4: Safely executes approved data corrections and produces the final cleaned SOV.
    """

    def __init__(self):
        pass

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute controlled transformations based on human review decisions.

        Args:
            state (SOVProcessingState): Pipeline state containing review_decisions and recommendations.

        Returns:
            SOVProcessingState: Updated state with approved_transformations, audit_log, and final_output_path.
        """
        # --- PLACEHOLDER FOR PHASE 3+ IMPLEMENTATION ---
        # 1. Match state.review_decisions against state.recommendations.
        # 2. For 'approve': apply proposed_value; for 'edit': apply edited_value; for 'reject': skip.
        # 3. Apply changes to tabular dataset in memory / DataFrame.
        # 4. Generate Transformation records in state.approved_transformations.
        # 5. Append AuditEntry records to state.audit_log.
        # 6. Save final standardized SOV file to state.final_output_path.

        state.status = JobStatus.TRANSFORMING

        # Sample placeholder transformation for integration wiring
        for decision in state.review_decisions:
            if decision.decision in ("approve", "edit"):
                target_value = (
                    decision.edited_value
                    if decision.decision == "edit"
                    else "TRANSFORMED_VALUE"
                )
                transformation = Transformation(
                    row=decision.row,
                    field=decision.field,
                    before="RAW_VALUE",
                    after=target_value,
                    transformation=f"applied_{decision.decision}",
                    approved_by=decision.reviewer,
                    approved_at=datetime.now(timezone.utc),
                )
                state.approved_transformations.append(transformation)

                audit_record = AuditEntry(
                    job_id=state.job_id,
                    user_id=decision.reviewer,
                    action=f"applied_transformation_{decision.decision}",
                    source=f"Row {decision.row}, {decision.field}",
                    target=decision.field,
                    before="RAW_VALUE",
                    after=target_value,
                    approver=decision.reviewer,
                    timestamp=datetime.now(timezone.utc),
                )
                state.audit_log.append(audit_record)

        state.status = JobStatus.COMPLETED
        state.final_output_path = f"data/output/cleaned_sov_{state.job_id}.xlsx"
        return state
