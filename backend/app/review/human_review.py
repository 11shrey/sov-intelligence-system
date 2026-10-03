"""Human Review Service

Handles validation and ingestion of human review decisions (approve, reject, edit)
prior to triggering data transformations in Agent 4.

Contains two classes:

HumanReviewService (team — preserved as-is)
    Stateless service that ingests a ReviewSubmission (batch of row-level
    ReviewDecision objects) into the pipeline state.  Used by orchestration
    and the FastAPI layer.

HumanReview (Member 3 integration)
    Stateful session that manages per-field review of ReviewRecommendation
    objects and produces FieldReviewDecision records.  Supports accept(),
    reject(), edit(), and batch index-based helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

from app.models.review_models import (
    DecisionType,
    FieldReviewDecision,
    ReviewRecommendation,
    ReviewDecision,
    ReviewSubmission,
)
from app.orchestration.state import SOVProcessingState, JobStatus


# ---------------------------------------------------------------------------
# Team class — preserved unchanged
# ---------------------------------------------------------------------------

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

    def get_pending_review_items(self, state: SOVProcessingState) -> Dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Member 3 integration — field-mapping review session
# ---------------------------------------------------------------------------

@dataclass
class ReviewSessionEntry:
    """
    Holds a single ReviewRecommendation and (optionally) its FieldReviewDecision.

    decision is None until the human explicitly provides one.
    That is the PENDING state — it is never auto-filled.
    """

    recommendation: ReviewRecommendation
    decision: Optional[FieldReviewDecision] = dc_field(default=None)

    @property
    def is_pending(self) -> bool:
        """True when no decision has been recorded yet."""
        return self.decision is None


class HumanReview:
    """
    Manages human review of one or more AI field-mapping recommendations.

    Usage (single recommendation)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        hr = HumanReview()
        decision = hr.accept(recommendation, approver="Alice")
        decision = hr.reject(recommendation, approver="Alice")
        decision = hr.edit(recommendation, edited_value=1_000_000, approver="Alice")

    Usage (batch / session)
    ~~~~~~~~~~~~~~~~~~~~~~~~
        hr = HumanReview(recommendations=[rec1, rec2, rec3])
        hr.accept_by_index(0, approver="Alice")
        hr.reject_by_index(2, approver="Alice")
        # rec2 remains PENDING until explicitly decided

    Design notes
    ~~~~~~~~~~~~
    - All three action methods (accept / reject / edit) are stateless helpers:
      they take a ReviewRecommendation and return a fresh FieldReviewDecision
      without touching the input object.
    - The session (self._entries) is opt-in: pass recommendations= to __init__
      if you want to track pending state across multiple items.
    """

    def __init__(
        self, recommendations: Optional[List[ReviewRecommendation]] = None
    ) -> None:
        """
        Parameters
        ----------
        recommendations:
            Optional initial list of ReviewRecommendations to track in this
            session.  Each starts as PENDING (decision=None).
        """
        self._entries: List[ReviewSessionEntry] = []
        if recommendations:
            for rec in recommendations:
                self._entries.append(ReviewSessionEntry(recommendation=rec))

    # ------------------------------------------------------------------
    # Stateless decision helpers
    # ------------------------------------------------------------------

    def accept(
        self, recommendation: ReviewRecommendation, approver: str
    ) -> FieldReviewDecision:
        """
        Create an ACCEPT FieldReviewDecision for the given ReviewRecommendation.

        The original ReviewRecommendation object is NOT modified.
        edited_value is always None for ACCEPT.

        Parameters
        ----------
        recommendation : The AI recommendation being reviewed.
        approver       : Name / ID of the human reviewer (must not be blank).

        Returns
        -------
        FieldReviewDecision with decision=ACCEPT.

        Raises
        ------
        pydantic.ValidationError  if approver is blank.
        """
        return FieldReviewDecision(
            source_field=recommendation.source_field,
            target_field=recommendation.target_field,
            decision=DecisionType.ACCEPT,
            edited_value=None,
            approver=approver,
        )

    def reject(
        self, recommendation: ReviewRecommendation, approver: str
    ) -> FieldReviewDecision:
        """
        Create a REJECT FieldReviewDecision for the given ReviewRecommendation.

        The original ReviewRecommendation object is NOT modified.
        A rejected recommendation must NOT be treated as an approved
        transformation — Agent 4 will skip REJECT decisions.

        Parameters
        ----------
        recommendation : The AI recommendation being reviewed.
        approver       : Name / ID of the human reviewer (must not be blank).

        Returns
        -------
        FieldReviewDecision with decision=REJECT.

        Raises
        ------
        pydantic.ValidationError  if approver is blank.
        """
        return FieldReviewDecision(
            source_field=recommendation.source_field,
            target_field=recommendation.target_field,
            decision=DecisionType.REJECT,
            edited_value=None,
            approver=approver,
        )

    def edit(
        self,
        recommendation: ReviewRecommendation,
        edited_value: object,
        approver: str,
    ) -> FieldReviewDecision:
        """
        Create an EDIT FieldReviewDecision for the given ReviewRecommendation.

        The reviewer supplies a corrected value that overrides the agent's
        recommendation.  The original ReviewRecommendation object is NOT modified.

        Parameters
        ----------
        recommendation : The AI recommendation being reviewed.
        edited_value   : The reviewer's corrected value.  Must NOT be None.
        approver       : Name / ID of the human reviewer (must not be blank).

        Returns
        -------
        FieldReviewDecision with decision=EDIT and the provided edited_value.

        Raises
        ------
        ValueError                if edited_value is None (EDIT requires a value).
        pydantic.ValidationError  if approver is blank or Pydantic rejects input.
        """
        if edited_value is None:
            raise ValueError(
                "EDIT requires an edited_value — use accept() or reject() "
                "if you do not want to supply a corrected value."
            )
        return FieldReviewDecision(
            source_field=recommendation.source_field,
            target_field=recommendation.target_field,
            decision=DecisionType.EDIT,
            edited_value=edited_value,
            approver=approver,
        )

    # ------------------------------------------------------------------
    # Session / batch helpers
    # ------------------------------------------------------------------

    def add_recommendation(self, recommendation: ReviewRecommendation) -> int:
        """
        Add a ReviewRecommendation to the session and return its index.

        The new entry starts as PENDING (no decision yet).
        """
        entry = ReviewSessionEntry(recommendation=recommendation)
        self._entries.append(entry)
        return len(self._entries) - 1

    def accept_by_index(self, index: int, approver: str) -> FieldReviewDecision:
        """Record an ACCEPT decision for the entry at *index*."""
        entry = self._get_entry(index)
        entry.decision = self.accept(entry.recommendation, approver)
        return entry.decision

    def reject_by_index(self, index: int, approver: str) -> FieldReviewDecision:
        """Record a REJECT decision for the entry at *index*."""
        entry = self._get_entry(index)
        entry.decision = self.reject(entry.recommendation, approver)
        return entry.decision

    def edit_by_index(
        self, index: int, edited_value: object, approver: str
    ) -> FieldReviewDecision:
        """Record an EDIT decision for the entry at *index*."""
        entry = self._get_entry(index)
        entry.decision = self.edit(entry.recommendation, edited_value, approver)
        return entry.decision

    # ------------------------------------------------------------------
    # Session queries
    # ------------------------------------------------------------------

    @property
    def entries(self) -> List[ReviewSessionEntry]:
        """All entries in this review session (decided + pending)."""
        return list(self._entries)

    @property
    def pending(self) -> List[ReviewSessionEntry]:
        """Entries that have NOT yet received a decision."""
        return [e for e in self._entries if e.is_pending]

    @property
    def decided(self) -> List[ReviewSessionEntry]:
        """Entries that HAVE received a decision."""
        return [e for e in self._entries if not e.is_pending]

    @property
    def decisions(self) -> List[FieldReviewDecision]:
        """All FieldReviewDecisions recorded so far (excludes pending entries)."""
        return [e.decision for e in self._entries if e.decision is not None]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_entry(self, index: int) -> ReviewSessionEntry:
        """Return entry by index with a friendly error on out-of-range."""
        if not (0 <= index < len(self._entries)):
            raise IndexError(
                f"No recommendation at index {index}. "
                f"Session has {len(self._entries)} entry/entries."
            )
        return self._entries[index]

