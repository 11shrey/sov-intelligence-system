"""Agent 1: Sheet Intelligence Agent

Responsible for:
- Inspecting multi-tab Excel workbooks.
- Identifying candidate SOV property schedule sheets.
- Detecting the true table header row (skipping banner/metadata rows).
- Computing confidence scores and reasoning for each sheet.
"""

from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.sheet_models import SheetAnalysis


class SheetIntelligenceAgent:
    """
    Agent 1: Evaluates uploaded Excel workbooks to identify the primary SOV sheet
    and its corresponding header row.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute sheet intelligence analysis on the workbook specified in state.file_info.

        Args:
            state (SOVProcessingState): Current pipeline state with uploaded file info.

        Returns:
            SOVProcessingState: Updated state with sheet_analysis, selected_sheet, and header_row.
        """
        # --- PLACEHOLDER FOR PHASE 3+ IMPLEMENTATION ---
        # 1. Read workbook sheet names and sample rows using excel_service.
        # 2. Score each sheet based on column patterns (Address, TIV, Building Value, Occupancy).
        # 3. Detect candidate header row index.
        # 4. Populate state.sheet_analysis and set state.selected_sheet / state.header_row.

        # Sample placeholder output for integration wiring
        if not state.sheet_analysis:
            placeholder_analysis = SheetAnalysis(
                sheet_name=state.metadata.get("default_sheet", "Sheet1"),
                is_candidate=True,
                header_row=0,
                confidence=0.95,
                reasoning="Placeholder: Detected property schedule keyword patterns in sheet headers.",
            )
            state.sheet_analysis = [placeholder_analysis]
            state.selected_sheet = placeholder_analysis.sheet_name
            state.header_row = placeholder_analysis.header_row

        state.status = JobStatus.SHEET_ANALYZED
        return state
