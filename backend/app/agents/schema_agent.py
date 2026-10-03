"""Agent 2: Schema Mapping Agent

Responsible for:
- Reading raw column headers from the selected sheet.
- Mapping each raw header to one of the 17 standard SOV target fields.
- Computing matching confidence scores and specifying the method (exact, fuzzy, LLM semantic).
"""

from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.schema_models import SchemaMapping, TARGET_SOV_FIELDS, TargetSOVField


class SchemaMappingAgent:
    """
    Agent 2: Maps source workbook column headers to the canonical 17 SOV schema fields.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute schema mapping on the selected sheet.

        Args:
            state (SOVProcessingState): Pipeline state containing selected_sheet and header_row.

        Returns:
            SOVProcessingState: Updated state with schema_mappings populated.
        """
        # --- PLACEHOLDER FOR PHASE 3+ IMPLEMENTATION ---
        # 1. Extract raw column headers from the selected sheet.
        # 2. Perform exact and fuzzy dictionary lookups against TARGET_SOV_FIELDS.
        # 3. Use LLM semantic reasoning for ambiguous or complex column headers.
        # 4. Generate SchemaMapping objects and populate state.schema_mappings.

        # Sample placeholder output for integration wiring
        if not state.schema_mappings:
            placeholder_mappings = [
                SchemaMapping(
                    source_column="Location ID",
                    target_field=TargetSOVField.REFERENCE.value,
                    confidence=0.98,
                    method="fuzzy_match",
                    reasoning="Placeholder: Direct match to reference field.",
                ),
                SchemaMapping(
                    source_column="Street Address",
                    target_field=TargetSOVField.ADDRESS.value,
                    confidence=0.99,
                    method="fuzzy_match",
                    reasoning="Placeholder: Standard address column.",
                ),
                SchemaMapping(
                    source_column="Bldg Value ($)",
                    target_field=TargetSOVField.BUILDING_VALUE.value,
                    confidence=0.96,
                    method="llm_semantic",
                    reasoning="Placeholder: Currency value mapped to building limit.",
                ),
            ]
            state.schema_mappings = placeholder_mappings

        state.status = JobStatus.SCHEMA_MAPPED
        return state
