"""Agent 3: Data Quality & Reasoning Agent

Responsible for:
- Scanning the mapped tabular SOV data for data anomalies and rule violations.
- Identifying missing mandatory fields, invalid postal codes, currency formatting glitches, etc.
- Generating actionable recommendations with proposed values for human review.
"""

from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.quality_models import QualityIssue, Recommendation


class DataQualityAgent:
    """
    Agent 3: Performs semantic and deterministic data quality inspection and proposes fixes.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute data quality analysis and generate proposed recommendations.

        Args:
            state (SOVProcessingState): Pipeline state with mapped schema and tabular data.

        Returns:
            SOVProcessingState: Updated state with quality_issues and recommendations.
        """
        # --- PLACEHOLDER FOR PHASE 3+ IMPLEMENTATION ---
        # 1. Validate data types and formats (e.g. zip codes, currency numbers, dates).
        # 2. Check domain lookups (ISO occupancy codes, construction types).
        # 3. Detect anomalies using rule engines + LLM reasoning.
        # 4. Populate state.quality_issues and state.recommendations.

        # Sample placeholder output for integration wiring
        if not state.quality_issues and not state.recommendations:
            sample_issue = QualityIssue(
                row=2,
                field="Zip",
                issue="Missing leading zero in 5-digit US postal code",
                severity="warning",
                current_value="7030",
                recommendation="Prepend '0' to format valid 5-digit zip code",
                confidence=0.99,
                reasoning="Placeholder: New Jersey postal codes start with '07...'",
            )
            sample_rec = Recommendation(
                row=2,
                field="Zip",
                action="fix_zip",
                current_value="7030",
                proposed_value="07030",
                confidence=0.99,
                reasoning="Placeholder: Format normalized to standard 5-digit zip.",
            )
            state.quality_issues = [sample_issue]
            state.recommendations = [sample_rec]

        state.status = JobStatus.AWAITING_REVIEW
        return state
