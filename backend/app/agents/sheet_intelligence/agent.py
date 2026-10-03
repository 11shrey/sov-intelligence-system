"""Agent 1 (Sheet Intelligence) Pipeline Coordinator.

Orchestrates:
Universal Ingestion -> Semantic Concept Detection -> Header Row Detection ->
Primary Table Selection -> Packaging Agent 1 -> Agent 2 Handoff Contract.
"""

from pathlib import Path
from typing import Any

from app.agents.sheet_intelligence.contracts import (
    Agent1HandoffResult,
    SemanticEvidenceItem,
    SheetEvaluationAudit,
)
from app.agents.sheet_intelligence.detection import HeaderDetector
from app.agents.sheet_intelligence.ingestion import UniversalIngestor
from app.agents.sheet_intelligence.scoring import PrimaryTableSelector
from app.agents.sheet_intelligence.semantics import SemanticDetector


class SheetIntelligenceEngine:
    """Agent 1 Pipeline Engine.

    Coordinates deterministic universal ingestion, header discovery, table selection,
    and packaging of the final handoff result for Agent 2.
    """

    DEFAULT_MAX_SAMPLE_ROWS: int = 5

    def __init__(
        self,
        universal_ingestor: UniversalIngestor | None = None,
        semantic_detector: SemanticDetector | None = None,
        header_detector: HeaderDetector | None = None,
        table_selector: PrimaryTableSelector | None = None,
    ) -> None:
        self.universal_ingestor = universal_ingestor or UniversalIngestor()
        self.semantic_detector = semantic_detector or SemanticDetector()
        self.header_detector = header_detector or HeaderDetector(
            semantic_detector=self.semantic_detector
        )
        self.table_selector = table_selector or PrimaryTableSelector(
            header_detector=self.header_detector
        )

    def process(
        self,
        file_path: str | Path,
        job_id: str = "default_job",
        max_sample_rows: int = DEFAULT_MAX_SAMPLE_ROWS,
    ) -> Agent1HandoffResult:
        """Run complete Agent 1 analysis on a source file and produce the Agent 2 handoff contract."""
        path = Path(file_path)

        # Step 1: Universal Ingestion
        workbook = self.universal_ingestor.ingest(path)

        # Step 2: Primary Sheet / Table Selection
        selection_res = self.table_selector.select_primary_table(workbook)

        # Build SheetEvaluationAudit summaries
        all_sheets_audit: list[SheetEvaluationAudit] = [
            SheetEvaluationAudit(
                sheet_name=cand.sheet_name,
                is_candidate=cand.is_candidate,
                header_row=cand.header_row,
                confidence=cand.header_confidence,
                final_score=cand.final_score,
                semantic_concept_count=cand.semantic_concept_count,
                data_density=cand.data_density,
                usable_records=cand.usable_records,
                reasoning=cand.reasoning,
            )
            for cand in selection_res.candidates
        ]

        # Case A: No valid SOV table found
        if selection_res.selected_sheet is None:
            return Agent1HandoffResult(
                job_id=job_id,
                source_file=path.name,
                file_type=workbook.file_type,
                selected_sheet=None,
                header_row=None,
                confidence=0.0,
                raw_headers=[],
                sample_rows=[],
                total_rows=0,
                all_sheets_evaluated=all_sheets_audit,
                semantic_evidence=[],
                reasoning=selection_res.reasoning,
            )

        # Case B: Valid SOV table selected
        selected_grid = workbook.tables[selection_res.selected_sheet]
        raw_rows = selected_grid.matrix
        header_row_idx = selection_res.selected_header_row
        raw_headers = selection_res.raw_headers
        num_cols = len(raw_headers)

        # Calculate total_rows: data rows beneath header, excluding header
        if header_row_idx is not None:
            total_data_rows = max(0, len(raw_rows) - (header_row_idx + 1))
            start_row = header_row_idx + 1
            end_row = min(start_row + max_sample_rows, len(raw_rows))
            extracted_samples: list[list[Any]] = []

            for r in raw_rows[start_row:end_row]:
                # Align sample cells with raw_headers length
                aligned = [
                    r[i] if i < len(r) else None for i in range(num_cols)
                ]
                extracted_samples.append(aligned)
        else:
            total_data_rows = 0
            extracted_samples = []

        # Extract semantic evidence per raw header column
        semantic_evidence: list[SemanticEvidenceItem] = []
        for col_idx, col_name in enumerate(raw_headers):
            cell_det = self.semantic_detector.detect_cell(col_name)
            detected_concept_ids = [
                mc.concept for mc in cell_det.matched_concepts
            ]
            first_alias = (
                cell_det.matched_concepts[0].alias
                if cell_det.matched_concepts
                else None
            )

            semantic_evidence.append(
                SemanticEvidenceItem(
                    column_index=col_idx,
                    raw_text=col_name,
                    detected_concepts=detected_concept_ids,
                    matched_alias=first_alias,
                    is_ambiguous=cell_det.is_ambiguous,
                )
            )

        return Agent1HandoffResult(
            job_id=job_id,
            source_file=path.name,
            file_type=workbook.file_type,
            selected_sheet=selection_res.selected_sheet,
            header_row=header_row_idx,
            confidence=selection_res.confidence,
            raw_headers=raw_headers,
            sample_rows=extracted_samples,
            total_rows=total_data_rows,
            all_sheets_evaluated=all_sheets_audit,
            semantic_evidence=semantic_evidence,
            is_near_tie=selection_res.is_near_tie,
            reasoning=selection_res.reasoning,
        )


def analyze_file(
    file_path: str | Path,
    job_id: str = "default_job",
    max_sample_rows: int = SheetIntelligenceEngine.DEFAULT_MAX_SAMPLE_ROWS,
) -> Agent1HandoffResult:
    """Public entry point for Agent 1 (Sheet Intelligence).

    Orchestrates universal ingestion, semantic concept detection, header row detection,
    primary table selection, and packaging into the Agent 2 handoff contract.

    Args:
        file_path: Path to the target source file (.xlsx, .csv, .json).
        job_id: Unique job execution identifier.
        max_sample_rows: Maximum data rows to sample beneath the header.

    Returns:
        Agent1HandoffResult: Validated Pydantic handoff contract ready for Agent 2.
    """
    engine = SheetIntelligenceEngine()
    return engine.process(
        file_path=file_path, job_id=job_id, max_sample_rows=max_sample_rows
    )

