"""Agent 1: Sheet Intelligence Agent.

Responsible for:
- Inspecting multi-tab Excel workbooks, CSV, TSV, and JSON files.
- Identifying candidate SOV property schedule sheets.
- Detecting the true table header row (0-indexed, matching pandas header=N).
- Computing confidence scores and reasoning for each sheet.
"""

from __future__ import annotations

import re
from typing import Any

from app.models.sheet_models import SheetAnalysis
from app.orchestration.state import SOVProcessingState, JobStatus
from app.services.excel_service import ExcelService


class SheetIntelligenceAgent:
    """Agent 1: identifies the primary SOV sheet and header row."""

    # Canonical SOV concepts mapped to distinct aliases for token matching
    SOV_CONCEPT_ALIASES: dict[str, list[str]] = {
        "reference": [
            "reference", "ref", "ref #", "ref no", "loc #", "loc id", "loc num",
            "location id", "location #", "location number", "prop id", "property id",
            "site id", "item #", "item no", "record #", "loc", "location"
        ],
        "address": [
            "address", "street address", "location address", "property address",
            "street", "addr", "site address", "physical address", "loc address", "premises address"
        ],
        "city": ["city", "municipality", "town"],
        "state": ["state", "province", "st"],
        "zip": ["zip", "zipcode", "zip code", "postal code", "postal", "postcode", "zip/postal", "postalcode"],
        "county": ["county", "parish"],
        "country": ["country", "nation"],
        "building_value": [
            "building value", "bldg value", "building limit", "bldg limit",
            "building", "bldg", "structure value", "building replacement cost",
            "building coverage", "bldg val", "building cost", "building amount"
        ],
        "contents": [
            "contents", "contents value", "contents limit", "bpp", "business personal property",
            "personal property", "contents val", "bpp limit", "bpp value", "contents amount"
        ],
        "bi": [
            "bi", "business interruption", "bi limit", "bi value", "business income",
            "time element", "gross earnings", "rents", "rental value", "bi amount"
        ],
        "tiv": [
            "tiv", "total insured value", "total value", "total limit", "total property value",
            "total sov value"
        ],
        "occupancy": [
            "occupancy", "occupancy description", "occupancy type", "occupancy code",
            "use", "usage", "occ", "tenant", "business description", "occupancy desc"
        ],
        "construction": [
            "construction", "construction type", "const", "const type", "iso construction",
            "bldg construction", "building construction", "construction class"
        ],
        "storeys": [
            "storeys", "stories", "floors", "num stories", "number of stories",
            "number of storeys", "story count", "no of stories", "num storeys", "no of storeys"
        ],
        "number_of_buildings": [
            "number of buildings", "num buildings", "bldg count", "building count",
            "buildings", "no of bldgs", "no of buildings", "# of buildings", "num bldgs"
        ],
        "year_built": [
            "year built", "built year", "yr built", "built", "construction year", "year constructed"
        ],
        "fire_sprinklers": [
            "fire sprinklers", "fire sprinkler", "sprinklers", "sprinkler", "sprinklered",
            "sprinkler (y/n)", "sprinklers (y/n)", "fire sprinklers (y/n)", "sprinkler %",
            "sprinklers y/n", "sprinkler y/n"
        ],
        "other": ["other", "other value", "misc value", "additional info", "other limit"]
    }

    # Words that strongly indicate non-data sheets using word-boundary matching
    REJECT_TERMS = {
        "instruction",
        "instructions",
        "cover",
        "cover page",
        "summary",
        "dashboard",
        "notes",
        "note",
        "readme",
        "glossary",
        "legend",
        "toc",
        "table of contents",
    }

    def __init__(self, model_name: str = "deterministic"):
        self.model_name = model_name
        self.excel_service = ExcelService()

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """Run sheet intelligence analysis on the uploaded workbook or dataset."""
        file_path = self._get_file_path(state)
        sheet_names = self.excel_service.get_sheet_names(file_path)

        analyses_with_counts: list[tuple[SheetAnalysis, int]] = []
        analyses: list[SheetAnalysis] = []

        for sheet_name in sheet_names:
            rows = self.excel_service.read_sheet_sample(
                file_path,
                sheet_name,
                max_rows=30,
            )

            analysis, data_row_count = self._analyze_sheet(
                sheet_name=sheet_name,
                rows=rows,
            )

            analyses.append(analysis)
            analyses_with_counts.append((analysis, data_row_count))

        selected = self._select_primary_sheet(analyses_with_counts)
        state.sheet_analysis = analyses

        if selected is not None:
            state.selected_sheet = selected.sheet_name
            state.header_row = selected.header_row
            state.status = JobStatus.SHEET_ANALYZED
        else:
            state.selected_sheet = None
            state.header_row = None
            state.status = JobStatus.SHEET_ANALYZED
            state.errors.append("No valid SOV candidate sheet detected in the uploaded file.")

        return state

    def _get_file_path(self, state: SOVProcessingState) -> str:
        """Extract the uploaded file path from the shared processing state."""
        if not state.file_info:
            raise ValueError("No uploaded file information found in processing state.")

        file_path = state.file_info.file_path
        if not file_path:
            raise ValueError("No uploaded file path found in processing state.")

        return str(file_path)

    def _analyze_sheet(
        self,
        sheet_name: str,
        rows: list[list[Any]],
    ) -> tuple[SheetAnalysis, int]:
        """Analyse one sheet and produce its SheetAnalysis alongside data row count."""
        if not rows:
            analysis = SheetAnalysis(
                sheet_name=sheet_name,
                is_candidate=False,
                header_row=None,
                confidence=0.0,
                reasoning="The sheet is empty or contains no readable rows.",
            )
            return analysis, 0

        header_row, matched_headers, matched_concepts, header_score = self._detect_header_row(rows)

        reject_signal = self._is_rejected_sheet_name(sheet_name)

        data_score, data_row_count = self._calculate_data_score(rows, header_row)

        if header_row is None:
            is_candidate = False
            confidence = 0.0
        else:
            candidate_score = (header_score * 0.65) + (data_score * 0.35)
            if reject_signal:
                candidate_score *= 0.30

            is_candidate = (candidate_score >= 0.40) and (header_row is not None)
            confidence = max(0.0, min(1.0, candidate_score))

        reasoning = self._build_reasoning(
            sheet_name=sheet_name,
            header_row=header_row,
            matched_headers=matched_headers,
            matched_concepts=matched_concepts,
            header_score=header_score,
            data_score=data_score,
            reject_signal=reject_signal,
            is_candidate=is_candidate,
            confidence=confidence,
        )

        analysis = SheetAnalysis(
            sheet_name=sheet_name,
            is_candidate=is_candidate,
            header_row=header_row,
            confidence=confidence,
            reasoning=reasoning,
        )
        return analysis, data_row_count

    def _detect_header_row(
        self,
        rows: list[list[Any]],
    ) -> tuple[int | None, list[str], list[str], float]:
        """Find the 0-indexed row most likely to contain column headers.

        Only inspects the first 20 rows.
        Returns: (header_row, matched_headers, matched_concepts, header_score)
        """
        best_row_index: int | None = None
        best_matched_headers: list[str] = []
        best_matched_concepts: list[str] = []
        best_score = 0.0

        for row_idx, row in enumerate(rows[:20]):
            cell_values = [
                str(val).strip()
                for val in row
                if val is not None and str(val).strip()
            ]

            if not cell_values:
                continue

            # Track distinct SOV concepts matched in this row
            matched_concepts_map: dict[str, str] = {}  # concept -> cell_value

            for val in cell_values:
                concept = self._match_sov_concept(val)
                if concept and concept not in matched_concepts_map:
                    matched_concepts_map[concept] = val

            distinct_concepts = list(matched_concepts_map.keys())

            # If no SOV concept matched, this row cannot be a header
            if not distinct_concepts:
                continue

            # Concept score rewards distinct matched concepts (out of 5)
            concept_score = min(len(distinct_concepts) / 5.0, 1.0)

            # Structure score considers non-numeric header cells
            text_columns = sum(1 for val in cell_values if not self._looks_numeric(val))
            structure_score = min(text_columns / 4.0, 1.0)

            score = (concept_score * 0.80) + (structure_score * 0.20)

            if score > best_score:
                best_score = score
                best_row_index = row_idx
                best_matched_concepts = distinct_concepts
                best_matched_headers = list(matched_concepts_map.values())

        if best_score == 0.0 or best_row_index is None:
            return None, [], [], 0.0

        return best_row_index, best_matched_headers, best_matched_concepts, best_score

    def _calculate_data_score(
        self,
        rows: list[list[Any]],
        header_row: int | None,
    ) -> tuple[float, int]:
        """Estimate whether the rows following the detected header contain meaningful tabular data."""
        if header_row is None or header_row >= len(rows) - 1:
            return 0.0, 0

        data_rows = rows[header_row + 1 :]
        populated_rows = 0

        for row in data_rows:
            populated = sum(
                1 for value in row if value is not None and str(value).strip()
            )
            if populated >= 2:
                populated_rows += 1

        data_score = min(populated_rows / 10.0, 1.0)
        return data_score, populated_rows

    def _match_sov_concept(self, cell_value: str) -> str | None:
        """Match cell string to an SOV concept using token/word-boundary matching.

        Guarantees that 'Statement' does NOT match 'State', but 'Property State' does.
        """
        normalized = self._normalize_text(cell_value)
        if not normalized:
            return None

        for concept, aliases in self.SOV_CONCEPT_ALIASES.items():
            for alias in aliases:
                norm_alias = self._normalize_text(alias)
                # Word-boundary pattern: ensures full-token match
                pattern = r"(?<!\w)" + re.escape(norm_alias) + r"(?!\w)"
                if re.search(pattern, normalized):
                    return concept

        return None

    def _is_rejected_sheet_name(self, sheet_name: str) -> bool:
        """Check if sheet name matches rejection terms using word boundaries.

        Guarantees 'Coverage Schedule' is NOT rejected by 'cover'.
        """
        normalized = self._normalize_text(sheet_name)
        if not normalized:
            return False

        for term in self.REJECT_TERMS:
            norm_term = self._normalize_text(term)
            pattern = r"(?<!\w)" + re.escape(norm_term) + r"(?!\w)"
            if re.search(pattern, normalized):
                return True

        return False

    def _normalize_text(self, text: Any) -> str:
        """Normalize text by lowercasing and replacing punctuation/symbols with single spaces."""
        text_str = str(text).lower()
        # Keep letters, numbers, and '#' symbol (e.g. 'loc #', 'ref #')
        cleaned = re.sub(r"[^\w\s#]", " ", text_str)
        return re.sub(r"\s+", " ", cleaned).strip()

    def _looks_numeric(self, value: str) -> bool:
        """Return True if a value is primarily numeric/currency/percentage."""
        cleaned = re.sub(r"[,\s$%.\-()#]", "", str(value).strip())
        return bool(cleaned) and cleaned.isdigit()

    def _build_reasoning(
        self,
        sheet_name: str,
        header_row: int | None,
        matched_headers: list[str],
        matched_concepts: list[str],
        header_score: float,
        data_score: float,
        reject_signal: bool,
        is_candidate: bool,
        confidence: float,
    ) -> str:
        """Build clear, structured explanation of analysis and scoring."""
        if reject_signal:
            return (
                f"Sheet '{sheet_name}' matches non-data sheet naming conventions (reject signal). "
                f"Header row: {header_row}, header score: {header_score:.2f}, "
                f"data score: {data_score:.2f}, confidence: {confidence:.2f}."
            )

        if header_row is None:
            return (
                f"No SOV header terms detected in the first 20 rows of sheet '{sheet_name}'. "
                f"Header score: 0.00, data score: {data_score:.2f}."
            )

        if is_candidate:
            return (
                f"Candidate SOV schedule detected on sheet '{sheet_name}'. "
                f"Header row: {header_row} (0-indexed) with {len(matched_concepts)} distinct SOV concepts "
                f"[{', '.join(matched_concepts[:6])}] matching headers [{', '.join(matched_headers[:6])}]. "
                f"Header score: {header_score:.2f}, data score: {data_score:.2f}, confidence: {confidence:.2f}."
            )

        return (
            f"Insufficient SOV property schedule evidence for sheet '{sheet_name}'. "
            f"Header row: {header_row}, header score: {header_score:.2f}, "
            f"data score: {data_score:.2f}, confidence: {confidence:.2f}."
        )

    def _select_primary_sheet(
        self,
        analyses_with_counts: list[tuple[SheetAnalysis, int]],
    ) -> SheetAnalysis | None:
        """Select primary SOV sheet breaking ties with confidence, then data row count."""
        candidates = [
            (analysis, count)
            for analysis, count in analyses_with_counts
            if analysis.is_candidate and analysis.header_row is not None
        ]

        if not candidates:
            return None

        # Sort: 1) Confidence descending, 2) Data row count descending
        candidates.sort(key=lambda item: (item[0].confidence, item[1]), reverse=True)
        return candidates[0][0]