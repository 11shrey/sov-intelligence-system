"""Deterministic SOV Semantic Concept Detection Engine.

Provides tokenization, word-boundary regex matching, guard phrase suppression,
and distinct-concept diversity scoring.
"""

from collections.abc import Iterable
import re
from typing import Any

from app.agents.sheet_intelligence.semantics.concepts import (
    AMBIGUOUS_TERMS,
    CORE_CONCEPT_ALIASES,
    NEGATIVE_GUARDS,
)
from app.agents.sheet_intelligence.semantics.models import (
    CellDetection,
    MatchedConcept,
    RowDetection,
)


class SemanticDetector:
    """Deterministic, zero-LLM semantic concept detector for raw tabular cell text."""

    def __init__(self) -> None:
        self._compiled_core: list[tuple[str, str, re.Pattern[str]]] = []
        self._compiled_ambiguous: list[tuple[str, str, float, re.Pattern[str]]] = []
        self._compiled_guards: dict[str, list[re.Pattern[str]]] = {}
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Pre-compile all regex patterns with word boundaries, sorted by phrase length descending."""
        # 1. Compile Core Concept Patterns (multi-word first)
        flat_core: list[tuple[str, str]] = []
        for concept_id, aliases in CORE_CONCEPT_ALIASES.items():
            for alias in aliases:
                flat_core.append((concept_id, alias))

        # Sort longer phrases first so "building value" matches before "building"
        flat_core.sort(key=lambda item: len(item[1]), reverse=True)

        for concept_id, alias in flat_core:
            # Word boundary regex with whitespace normalization
            escaped = re.escape(alias).replace(r"\ ", r"\s+")
            pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            self._compiled_core.append((concept_id, alias, pattern))

        # 2. Compile Ambiguous Signal Patterns
        for term, meta in sorted(
            AMBIGUOUS_TERMS.items(), key=lambda x: len(x[0]), reverse=True
        ):
            escaped = re.escape(term).replace(r"\ ", r"\s+")
            pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            self._compiled_ambiguous.append(
                (meta["concept"], term, meta["confidence"], pattern)
            )

        # 3. Compile Negative Guards
        for concept_id, guard_words in NEGATIVE_GUARDS.items():
            self._compiled_guards[concept_id] = [
                re.compile(
                    rf"\b{re.escape(gw).replace(r'\ ', r'\s+')}\b",
                    re.IGNORECASE,
                )
                for gw in guard_words
            ]

    def normalize_text(self, cell_value: Any) -> str:
        """Normalize raw cell value strictly for detection matching without mutating source.

        Operations:
        1. Convert to string and lowercase.
        2. Replace hyphens and underscores with spaces.
        3. Remove common punctuation noise: ($), #, *, %, quotes, etc.
        4. Collapse multiple spaces into a single space and strip edges.
        """
        if cell_value is None:
            return ""

        text = str(cell_value).strip().lower()
        if not text:
            return ""

        # Replace dashes and underscores with spaces
        text = re.sub(r"[-_]+", " ", text)

        # Remove currency symbols and common header brackets/punctuation
        text = re.sub(r"[\$\(\)\[\]\{\}\#\*\%\:\;\"\'\?]", " ", text)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def detect_cell(self, cell_value: Any) -> CellDetection:
        """Analyze a single raw cell and identify matched semantic concepts or signals."""
        raw_str = str(cell_value) if cell_value is not None else None
        normalized = self.normalize_text(cell_value)

        if not normalized:
            return CellDetection(
                raw_text=raw_str,
                normalized_text="",
                matched_concepts=[],
                is_ambiguous=False,
            )

        matches: list[MatchedConcept] = []
        matched_concept_ids: set[str] = set()

        # Step 1: Check Core Definitive Concepts
        for concept_id, alias, pattern in self._compiled_core:
            # Check negative guards for this concept
            is_guarded = False
            if concept_id in self._compiled_guards:
                for guard_pat in self._compiled_guards[concept_id]:
                    if guard_pat.search(normalized):
                        is_guarded = True
                        break

            if is_guarded:
                continue

            if pattern.search(normalized):
                if concept_id not in matched_concept_ids:
                    match_type = (
                        "exact"
                        if normalized == alias
                        else ("phrase" if " " in alias else "alias")
                    )
                    matches.append(
                        MatchedConcept(
                            concept=concept_id,
                            alias=alias,
                            match_type=match_type,
                            confidence=1.0,
                        )
                    )
                    matched_concept_ids.add(concept_id)

        # If definitive core concepts were matched, return them without ambiguous fallback
        if matches:
            return CellDetection(
                raw_text=raw_str,
                normalized_text=normalized,
                matched_concepts=matches,
                is_ambiguous=False,
            )

        # Step 2: Check Ambiguous Terms (only if no definitive concept was found)
        ambiguous_matches: list[MatchedConcept] = []
        for concept_signal, term, confidence, pattern in self._compiled_ambiguous:
            if pattern.search(normalized):
                ambiguous_matches.append(
                    MatchedConcept(
                        concept=concept_signal,
                        alias=term,
                        match_type="alias",
                        confidence=confidence,
                    )
                )

        if ambiguous_matches:
            return CellDetection(
                raw_text=raw_str,
                normalized_text=normalized,
                matched_concepts=ambiguous_matches,
                is_ambiguous=True,
            )

        # No match found
        return CellDetection(
            raw_text=raw_str,
            normalized_text=normalized,
            matched_concepts=[],
            is_ambiguous=False,
        )

    def analyze_row(
        self, raw_cells: Iterable[Any], row_index: int | None = None
    ) -> RowDetection:
        """Perform semantic analysis across an entire row of cells.

        Computes:
        - Per-cell concept detections.
        - Distinct definitive concepts found.
        - Concept diversity score based on distinct concept count.
        - Ambiguous signals detected.
        """
        cells_list = list(raw_cells)
        cell_detections = [self.detect_cell(c) for c in cells_list]

        distinct_core: set[str] = set()
        ambiguous_signals: set[str] = set()

        for det in cell_detections:
            for mc in det.matched_concepts:
                if mc.concept in CORE_CONCEPT_ALIASES:
                    distinct_core.add(mc.concept)
                elif mc.concept.endswith("_signal"):
                    ambiguous_signals.add(mc.concept)

        sorted_distinct = sorted(distinct_core)
        concept_count = len(sorted_distinct)

        # Concept Diversity Score Formula:
        # A full SOV header typically spans >= 7 core concepts (e.g. ref, addr, city, state, zip, val_bldg, occ).
        # We compute: min(1.0, distinct_concepts / 7.0)
        diversity_score = round(min(1.0, concept_count / 7.0), 3)

        return RowDetection(
            row_index=row_index,
            raw_cells=cells_list,
            cell_detections=cell_detections,
            distinct_concepts=sorted_distinct,
            concept_count=concept_count,
            diversity_score=diversity_score,
            ambiguous_signals=sorted(ambiguous_signals),
        )
