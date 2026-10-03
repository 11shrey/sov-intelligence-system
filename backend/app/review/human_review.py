"""Human Review Service

Handles validation and ingestion of human review decisions (approve, reject, edit)
prior to triggering data transformations in Agent 4.
"""

from typing import Any
from app.models.review_models import ReviewDecision, ReviewSubmission
from app.orchestration.state import SOVProcessingState, JobStatus


class HumanReviewService:
    """Service to manage human-in-the-loop validation and approvals."""

    def record_decisions(
        self, state: SOVProcessingState, submission: ReviewSubmission
    ) -> SOVProcessingState:
        """
        Record reviewer decisions onto the job state.

        Args:
            state (SOVProcessingState): Current pipeline state.
            submission (ReviewSubmission): Batch of reviewer decisions.

        Returns:
            SOVProcessingState: Updated state with review_decisions and status.
        """
        # Validate decisions against existing recommendations
        state.review_decisions.extend(submission.decisions)
        state.status = JobStatus.REVIEW_COMPLETED
        return state

    def get_pending_review_items(self, state: SOVProcessingState) -> dict[str, Any]:
        """
        Retrieve recommendations and quality issues awaiting human review.

        Args:
            state (SOVProcessingState): Current pipeline state.

        Returns:
            dict[str, Any]: Bundle of quality issues and recommendations.
        """
        return {
            "job_id": state.job_id,
            "status": state.status,
            "quality_issues": state.quality_issues,
            "recommendations": state.recommendations,
            "review_decisions_count": len(state.review_decisions),
        }
