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

        Enforces the routing policy:
          - PASS: No issues created, continues automatically.
          - LOW: Recorded in audit information, excluded from human-review inbox.
          - MEDIUM: Included in human-review inbox (requires_human_review is True).
          - HIGH: Included in human-review inbox (requires_human_review is True).

        Args:
            state (SOVProcessingState): Current pipeline state.

        Returns:
            dict[str, Any]: Bundle of quality issues and recommendations awaiting human review.
        """
        def _requires_review(item: Any) -> bool:
            if hasattr(item, "requires_human_review"):
                return bool(getattr(item, "requires_human_review", False))
            if isinstance(item, dict):
                return bool(item.get("requires_human_review", False))
            return False

        pending_issues = [
            issue for issue in state.quality_issues
            if _requires_review(issue)
        ]

        if len(state.quality_issues) == len(state.recommendations):
            pending_recommendations = [
                rec
                for rec, issue in zip(state.recommendations, state.quality_issues)
                if _requires_review(issue)
            ]
        else:
            def _get_key(item: Any) -> tuple[Any, Any]:
                if hasattr(item, "row") and hasattr(item, "field"):
                    return (getattr(item, "row"), getattr(item, "field"))
                if isinstance(item, dict):
                    return (item.get("row"), item.get("field"))
                return (None, None)

            review_keys = {_get_key(issue) for issue in pending_issues}
            pending_recommendations = [
                rec
                for rec in state.recommendations
                if _get_key(rec) in review_keys
            ]

        return {
            "job_id": state.job_id,
            "status": state.status,
            "quality_issues": pending_issues,
            "recommendations": pending_recommendations,
            "review_decisions_count": len(state.review_decisions),
        }

