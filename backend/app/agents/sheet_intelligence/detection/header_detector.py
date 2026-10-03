"""Deterministic Header Row Detector for Agent 1.

Identifies the true SOV table header within a normalized 2D table by combining:
1. Semantic concept diversity from SemanticDetector.
2. Populated column count and label structure.
3. Post-header data density in rows directly below candidate rows.
4. Header-vs-data heuristics.
"""

from typing import Any

from app.agents.sheet_intelligence.detection.models import (
    CandidateRowDetail,
    HeaderDetectionResult,
)
from app.agents.sheet_intelligence.semantics import SemanticDetector


class HeaderDetector:
    """Evaluates candidate rows in a normalized table to locate the primary SOV header row."""

    DEFAULT_MAX_SCAN_ROWS: int = 30
    DEFAULT_MIN_CONFIDENCE: float = 0.35
    DENSITY_LOOKAHEAD_ROWS: int = 5

    def __init__(
        self,
        semantic_detector: SemanticDetector | None = None,
        max_scan_rows: int = DEFAULT_MAX_SCAN_ROWS,
        min_confidence_threshold: float = DEFAULT_MIN_CONFIDENCE,
    ) -> None:
        self.semantic_detector = semantic_detector or SemanticDetector()
        self.max_scan_rows = max_scan_rows
        self.min_confidence_threshold = min_confidence_threshold

    def detect_header_row(
        self, rows: list[list[Any]]
    ) -> HeaderDetectionResult:
        """Inspect the early row window of a table and return the most likely header row.

        Args:
            rows: 2D list of raw cell values from UniversalIngestor.

        Returns:
            HeaderDetectionResult: Detected header index, confidence, raw headers, and audit details.
        """
        if not rows:
            return HeaderDetectionResult(
                header_row=None,
                confidence=0.0,
                raw_headers=[],
                detected_concepts=[],
                reasoning=["Table contains 0 rows; no header possible."],
                candidate_rows=[],
            )

        total_rows = len(rows)
        scan_limit = min(self.max_scan_rows, total_rows)
        candidates: list[CandidateRowDetail] = []

        best_row_index: int | None = None
        best_score: float = -1.0
        best_reasoning: list[str] = []
        best_concepts: list[str] = []
        best_density: float = 0.0

        for r_idx in range(scan_limit):
            row = rows[r_idx]

            # Populated cells count
            populated_cells = [
                c for c in row if c is not None and str(c).strip() != ""
            ]
            pop_count = len(populated_cells)

            # Skip completely empty rows
            if pop_count == 0:
                continue

            # Run semantic concept detection on this row
            row_det = self.semantic_detector.analyze_row(row, row_index=r_idx)
            distinct_concepts = row_det.distinct_concepts
            concept_count = row_det.concept_count
            ambiguous_signals = row_det.ambiguous_signals

            # Calculate data-like cell ratio (numeric, pure dates, currency)
            data_like_count = sum(
                1 for c in populated_cells if self._is_data_like(c)
            )
            data_like_ratio = data_like_count / pop_count if pop_count > 0 else 0.0

            # Calculate post-header data density in next K rows
            density_below = self._calculate_post_header_density(
                rows=rows,
                header_row_index=r_idx,
                header_populated_count=pop_count,
            )

            # Compute deterministic candidate score
            score, reasoning = self._score_candidate(
                row_index=r_idx,
                pop_count=pop_count,
                concept_count=concept_count,
                distinct_concepts=distinct_concepts,
                ambiguous_signals=ambiguous_signals,
                density_below=density_below,
                data_like_ratio=data_like_ratio,
            )

            cand_detail = CandidateRowDetail(
                row_index=r_idx,
                distinct_concepts=distinct_concepts,
                concept_count=concept_count,
                populated_cells=pop_count,
                data_density_below=density_below,
                score=score,
                reasoning=reasoning,
            )
            candidates.append(cand_detail)

            # Eligibility requirements:
            # - At least 2 populated cells
            # - At least 1 core concept or ambiguous signal
            # - Must beat current best score
            has_sufficient_concepts = (
                concept_count >= 2
                or (concept_count >= 1 and len(ambiguous_signals) >= 1)
                or (concept_count >= 1 and pop_count >= 3 and density_below >= 0.5)
            )

            if pop_count >= 2 and has_sufficient_concepts and score > best_score:
                best_score = score
                best_row_index = r_idx
                best_reasoning = reasoning
                best_concepts = distinct_concepts
                best_density = density_below

        # Check against minimum confidence threshold
        if best_row_index is not None and best_score >= self.min_confidence_threshold:
            selected_row = rows[best_row_index]
            raw_headers = self._extract_raw_headers(selected_row)

            summary_reasoning = [
                f"Selected Row {best_row_index} with confidence {best_score:.2f}.",
                f"Detected {len(best_concepts)} core SOV concepts: {best_concepts}.",
                f"Post-header data density: {best_density:.2f} across subsequent rows.",
                *best_reasoning,
            ]

            return HeaderDetectionResult(
                header_row=best_row_index,
                confidence=best_score,
                raw_headers=raw_headers,
                detected_concepts=best_concepts,
                reasoning=summary_reasoning,
                candidate_rows=candidates,
            )

        # No candidate met the criteria
        return HeaderDetectionResult(
            header_row=None,
            confidence=0.0,
            raw_headers=[],
            detected_concepts=[],
            reasoning=[
                "No sufficiently strong SOV header candidate detected.",
                f"Highest candidate score was {best_score:.2f} (threshold: {self.min_confidence_threshold:.2f})."
                if best_score >= 0
                else "No non-empty candidate rows found.",
            ],
            candidate_rows=candidates,
        )

    def _score_candidate(
        self,
        row_index: int,
        pop_count: int,
        concept_count: int,
        distinct_concepts: list[str],
        ambiguous_signals: list[str],
        density_below: float,
        data_like_ratio: float,
    ) -> tuple[float, list[str]]:
        """Compute composite confidence score (0.0 to 1.0) and explainable rationale."""
        reasoning: list[str] = []

        # 1. Concept Diversity Component (0.0 to 1.0) - Weight: 0.45
        # 5 distinct concepts yields maximum concept score
        s_concept = min(1.0, concept_count / 5.0)
        reasoning.append(
            f"Concept diversity: {concept_count} concepts (score: {s_concept:.2f})"
        )

        # 2. Data Density Component (0.0 to 1.0) - Weight: 0.35
        s_density = density_below
        reasoning.append(
            f"Post-header data density: {density_below:.2f} (score: {s_density:.2f})"
        )

        # 3. Structure & Column Breadth Component (0.0 to 1.0) - Weight: 0.20
        # A typical SOV schedule has >= 4 columns
        s_structure = min(1.0, pop_count / 4.0)
        reasoning.append(
            f"Header structure: {pop_count} populated columns (score: {s_structure:.2f})"
        )

        # Base Weighted Score
        base_score = (
            0.45 * s_concept + 0.35 * s_density + 0.20 * s_structure
        )

        # Bonuses
        bonus = 0.0
        if ambiguous_signals and concept_count >= 1:
            signal_bonus = min(0.10, len(ambiguous_signals) * 0.05)
            bonus += signal_bonus
            reasoning.append(
                f"Bonus for ambiguous signals {ambiguous_signals}: +{signal_bonus:.2f}"
            )

        # Penalties
        penalty = 0.0

        # Penalty A: Single concept or metadata row
        if concept_count < 2 and not ambiguous_signals:
            penalty += 0.35
            reasoning.append(
                f"Penalty for low concept diversity (< 2 concepts): -0.35"
            )

        # Penalty B: Few columns (< 3 columns)
        if pop_count < 3:
            penalty += 0.25
            reasoning.append(
                f"Penalty for narrow row (< 3 columns): -0.25"
            )

        # Penalty C: Data-like values (numeric/dates)
        if data_like_ratio > 0.30:
            data_penalty = round(data_like_ratio * 0.50, 2)
            penalty += data_penalty
            reasoning.append(
                f"Penalty for data-like values ({data_like_ratio:.1%}): -{data_penalty:.2f}"
            )

        # Penalty D: Slight depth penalty (0.003 per row)
        depth_penalty = round(row_index * 0.003, 3)
        penalty += depth_penalty

        final_score = round(max(0.0, min(1.0, base_score + bonus - penalty)), 3)
        reasoning.append(f"Composite confidence score: {final_score:.2f}")

        return final_score, reasoning

    def _calculate_post_header_density(
        self,
        rows: list[list[Any]],
        header_row_index: int,
        header_populated_count: int,
    ) -> float:
        """Calculate populated cell density in the rows directly underneath the candidate."""
        total_rows = len(rows)
        start_idx = header_row_index + 1
        end_idx = min(start_idx + self.DENSITY_LOOKAHEAD_ROWS, total_rows)

        if start_idx >= total_rows:
            # Candidate is the very last row in table: 0 data density below
            return 0.0

        lookahead_count = end_idx - start_idx
        if lookahead_count == 0 or header_populated_count == 0:
            return 0.0

        total_subsequent_populated = 0
        for i in range(start_idx, end_idx):
            sub_row = rows[i]
            total_subsequent_populated += sum(
                1 for c in sub_row if c is not None and str(c).strip() != ""
            )

        expected_cells = lookahead_count * header_populated_count
        density = total_subsequent_populated / expected_cells
        return round(min(1.0, density), 3)

    def _is_data_like(self, cell_value: Any) -> bool:
        """Detect whether a cell looks like raw business data (numbers, dates) rather than a label."""
        if cell_value is None:
            return False

        val_str = str(cell_value).strip()
        if not val_str:
            return False

        # Numbers (int, float, currency digits)
        clean_num = val_str.replace(",", "").replace("$", "").replace("%", "")
        try:
            float(clean_num)
            return True
        except ValueError:
            pass

        # Pure numeric strings or postal codes
        if clean_num.isdigit():
            return True

        return False

    def _extract_raw_headers(self, row: list[Any]) -> list[str]:
        """Extract verbatim raw headers up to the last populated column."""
        # Find index of last populated cell
        last_idx = -1
        for idx, cell in enumerate(row):
            if cell is not None and str(cell).strip() != "":
                last_idx = idx

        if last_idx == -1:
            return []

        # Return verbatim string representations
        headers: list[str] = []
        for cell in row[: last_idx + 1]:
            headers.append("" if cell is None else str(cell))

        return headers
