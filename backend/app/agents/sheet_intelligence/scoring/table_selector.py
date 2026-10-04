"""Deterministic Primary Sheet and Table Selector for Agent 1.

Evaluates all candidate sheets/tables in an uploaded file, integrates header-row
and semantic detection evidence, applies word-boundary sheet name signals, and
resolves near ties deterministically.
"""

import re
from typing import Any, Final

from app.agents.sheet_intelligence.detection import (
    HeaderDetectionResult,
    HeaderDetector,
)
from app.agents.sheet_intelligence.ingestion import IngestedWorkbook
from app.agents.sheet_intelligence.scoring.models import (
    TableCandidateSummary,
    TableSelectionResult,
)

# Positive sheet name signals with word boundaries
POSITIVE_SHEET_SIGNALS: Final[list[str]] = [
    "property schedule",
    "location data",
    "exposure data",
    "schedule of values",
    "property",
    "properties",
    "locations",
    "location",
    "sov",
    "schedule",
    "exposure",
]

# Negative sheet name signals with word boundaries
NEGATIVE_SHEET_SIGNALS: Final[list[str]] = [
    "table of contents",
    "instructions",
    "instruction",
    "cover",
    "summary",
    "notes",
    "note",
    "readme",
    "contents",
    "toc",
    "index",
    "glossary",
]


class PrimaryTableSelector:
    """Evaluates candidate tables across an ingested file to select the primary SOV table."""

    NEAR_TIE_THRESHOLD: float = 0.05
    MIN_SELECTION_THRESHOLD: float = 0.40

    def __init__(
        self,
        header_detector: HeaderDetector | None = None,
        min_selection_threshold: float = MIN_SELECTION_THRESHOLD,
        near_tie_threshold: float = NEAR_TIE_THRESHOLD,
    ) -> None:
        self.header_detector = header_detector or HeaderDetector()
        self.min_selection_threshold = min_selection_threshold
        self.near_tie_threshold = near_tie_threshold

        # Pre-compile sheet name regex patterns with word boundaries
        self._compiled_positive = [
            re.compile(
                rf"\b{re.escape(sig).replace(r'\ ', r'\s+')}\b", re.IGNORECASE
            )
            for sig in sorted(
                POSITIVE_SHEET_SIGNALS, key=lambda s: len(s), reverse=True
            )
        ]
        self._compiled_negative = [
            re.compile(
                rf"\b{re.escape(sig).replace(r'\ ', r'\s+')}\b", re.IGNORECASE
            )
            for sig in sorted(
                NEGATIVE_SHEET_SIGNALS, key=lambda s: len(s), reverse=True
            )
        ]

    def select_primary_table(
        self, workbook_or_tables: IngestedWorkbook | dict[str, list[list[Any]]]
    ) -> TableSelectionResult:
        """Evaluate each table/sheet and determine the primary SOV property schedule."""
        if isinstance(workbook_or_tables, IngestedWorkbook):
            tables_dict = workbook_or_tables.to_dict()
        else:
            tables_dict = workbook_or_tables

        if not tables_dict:
            return TableSelectionResult(
                selected_sheet=None,
                selected_header_row=None,
                confidence=0.0,
                raw_headers=[],
                detected_concepts=[],
                is_near_tie=False,
                near_tie_candidates=[],
                candidates=[],
                reasoning=["Workbook contains 0 tables or sheets."],
            )

        candidate_summaries: list[TableCandidateSummary] = []
        detection_results: dict[str, HeaderDetectionResult] = {}

        # Step 1: Evaluate each sheet independently
        for sheet_name, rows in tables_dict.items():
            hdr_res = self.header_detector.detect_header_row(rows)
            detection_results[sheet_name] = hdr_res

            summary = self._evaluate_table(sheet_name=sheet_name, rows=rows, hdr_res=hdr_res)
            candidate_summaries.append(summary)

        # Step 2: Rank qualifying candidates
        qualifying = [
            c for c in candidate_summaries
            if c.is_candidate and c.final_score >= self.min_selection_threshold
        ]

        if not qualifying:
            highest_score = max((c.final_score for c in candidate_summaries), default=0.0)
            return TableSelectionResult(
                selected_sheet=None,
                selected_header_row=None,
                confidence=0.0,
                raw_headers=[],
                detected_concepts=[],
                is_near_tie=False,
                near_tie_candidates=[],
                candidates=candidate_summaries,
                reasoning=[
                    "No sheet qualified as a primary SOV property schedule.",
                    f"Highest table score was {highest_score:.2f} (threshold: {self.min_selection_threshold:.2f}).",
                ],
            )

        # Sort qualifying candidates by score descending
        qualifying.sort(key=lambda c: c.final_score, reverse=True)

        winner = qualifying[0]
        is_near_tie = False
        near_tie_candidates: list[str] = []
        selection_confidence = winner.final_score
        selection_reasoning: list[str] = []

        # Step 3: Near-Tie Detection and Deterministic Resolution
        if len(qualifying) >= 2:
            runner_up = qualifying[1]
            diff = abs(winner.final_score - runner_up.final_score)

            if diff < self.near_tie_threshold:
                is_near_tie = True
                near_tie_candidates = [winner.sheet_name, runner_up.sheet_name]

                # Ambiguity penalty for close decision
                selection_confidence = round(winner.final_score * 0.90, 3)

                # Deterministic tie-breaker rules
                tie_reason = self._resolve_tie_breaker(winner, runner_up)
                selection_reasoning.append(
                    f"Near tie detected between '{winner.sheet_name}' ({winner.final_score:.2f}) and "
                    f"'{runner_up.sheet_name}' ({runner_up.final_score:.2f}). Score diff: {diff:.3f} (< {self.near_tie_threshold:.2f})."
                )
                selection_reasoning.append(tie_reason)

        # Build final winning result
        win_hdr = detection_results[winner.sheet_name]
        selection_reasoning.insert(
            0,
            f"Selected sheet '{winner.sheet_name}' as primary SOV schedule with score {selection_confidence:.2f}."
        )
        selection_reasoning.append(
            f"Header detected at Row {winner.header_row} with {winner.semantic_concept_count} distinct concepts: {win_hdr.detected_concepts}."
        )
        selection_reasoning.append(
            f"Contains {winner.usable_records} usable records with post-header data density {winner.data_density:.2f}."
        )

        return TableSelectionResult(
            selected_sheet=winner.sheet_name,
            selected_header_row=winner.header_row,
            confidence=selection_confidence,
            raw_headers=win_hdr.raw_headers,
            detected_concepts=win_hdr.detected_concepts,
            is_near_tie=is_near_tie,
            near_tie_candidates=near_tie_candidates,
            candidates=candidate_summaries,
            reasoning=selection_reasoning,
        )

    def _evaluate_table(
        self, sheet_name: str, rows: list[list[Any]], hdr_res: HeaderDetectionResult
    ) -> TableCandidateSummary:
        """Compute table score and audit summary for a single sheet."""
        total_rows = len(rows)
        header_row = hdr_res.header_row
        header_conf = hdr_res.confidence
        concept_count = len(hdr_res.detected_concepts)

        if header_row is not None:
            usable_records = max(0, total_rows - (header_row + 1))
            # Retrieve data density from chosen candidate row
            data_density = 0.0
            for cand in hdr_res.candidate_rows:
                if cand.row_index == header_row:
                    data_density = cand.data_density_below
                    break
        else:
            usable_records = 0
            data_density = 0.0

        # Sheet name analysis
        sheet_score, name_reason = self._score_sheet_name(sheet_name)
        neg_penalty, neg_reason = self._check_negative_signals(sheet_name)

        # Composite table scoring
        reasoning: list[str] = []

        # 1. Header Confidence Component (Weight: 0.50)
        s_hdr = header_conf
        reasoning.append(f"Header confidence: {header_conf:.2f} (weight: 0.50)")

        # 2. Concept Diversity Component (Weight: 0.25)
        # 5 concepts yields max score
        s_concept = min(1.0, concept_count / 5.0)
        reasoning.append(f"Concept diversity: {concept_count} concepts (score: {s_concept:.2f}, weight: 0.25)")

        # 3. Data Density Component (Weight: 0.15)
        s_density = data_density
        reasoning.append(f"Data density below header: {data_density:.2f} (weight: 0.15)")

        # 4. Usable Records Component (Weight: 0.10)
        # 20 records yields max score
        s_records = min(1.0, usable_records / 20.0)
        reasoning.append(f"Usable records count: {usable_records} (score: {s_records:.2f}, weight: 0.10)")

        base_score = (
            0.50 * s_hdr + 0.25 * s_concept + 0.15 * s_density + 0.10 * s_records
        )

        # Modifiers
        bonus = sheet_score
        penalty = neg_penalty

        if name_reason:
            reasoning.append(name_reason)
        if neg_reason:
            reasoning.append(neg_reason)

        # Additional penalties
        if header_row is None:
            penalty += 0.50
            reasoning.append("Penalty for missing valid header: -0.50")
        elif usable_records == 0:
            penalty += 0.30
            reasoning.append("Penalty for 0 usable records below header: -0.30")
        has_sufficient_concepts = (
            concept_count >= 2
            or (concept_count >= 1 and header_conf >= 0.50)
        )
        if not has_sufficient_concepts:
            penalty += 0.25
            reasoning.append("Penalty for sparse concepts (< 2 concepts): -0.25")

        final_score = round(max(0.0, min(1.0, base_score + bonus - penalty)), 3)
        reasoning.append(f"Final sheet score: {final_score:.2f}")

        is_candidate = (
            header_row is not None
            and has_sufficient_concepts
            and final_score >= self.min_selection_threshold
        )

        return TableCandidateSummary(
            sheet_name=sheet_name,
            is_candidate=is_candidate,
            header_row=header_row,
            header_confidence=header_conf,
            semantic_concept_count=concept_count,
            data_density=data_density,
            sheet_name_score=sheet_score,
            negative_signal_penalty=neg_penalty,
            total_rows=total_rows,
            usable_records=usable_records,
            final_score=final_score,
            reasoning=reasoning,
        )

    def _score_sheet_name(self, sheet_name: str) -> tuple[float, str | None]:
        """Detect positive sheet name signals using word boundary matching."""
        clean_name = sheet_name.strip().lower()
        for pat in self._compiled_positive:
            if pat.search(clean_name):
                return 0.10, f"Positive sheet name signal matched: +0.10"
        return 0.0, None

    def _check_negative_signals(self, sheet_name: str) -> tuple[float, str | None]:
        """Detect negative sheet name signals using word boundary matching."""
        clean_name = sheet_name.strip().lower()
        for pat in self._compiled_negative:
            if pat.search(clean_name):
                return 0.25, f"Negative sheet name signal matched: -0.25"
        return 0.0, None

    def _resolve_tie_breaker(
        self, cand_a: TableCandidateSummary, cand_b: TableCandidateSummary
    ) -> str:
        """Deterministic tie-breaker explanation."""
        if cand_a.semantic_concept_count != cand_b.semantic_concept_count:
            winner = cand_a if cand_a.semantic_concept_count > cand_b.semantic_concept_count else cand_b
            return f"Tie-breaker 1 applied: '{winner.sheet_name}' has more distinct concepts ({winner.semantic_concept_count})."

        if abs(cand_a.data_density - cand_b.data_density) >= 0.05:
            winner = cand_a if cand_a.data_density > cand_b.data_density else cand_b
            return f"Tie-breaker 2 applied: '{winner.sheet_name}' has higher data density ({winner.data_density:.2f})."

        if cand_a.usable_records != cand_b.usable_records:
            winner = cand_a if cand_a.usable_records > cand_b.usable_records else cand_b
            return f"Tie-breaker 3 applied: '{winner.sheet_name}' has more usable records ({winner.usable_records})."

        return f"Tie-breaker 4 applied: '{cand_a.sheet_name}' preserved based on workbook tab order."
