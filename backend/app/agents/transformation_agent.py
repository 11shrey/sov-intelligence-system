"""Agent 4: Controlled Transformation Agent

Responsible for:
- Reading approved human review decisions from state.review_decisions.
- Applying data transformations deterministically (applying approved values or human edits).
- Generating transformation log entries (Transformation) and audit records (AuditEntry).
- Producing the final cleaned SOV output dataset.

Contains two classes:

ControlledTransformationAgent (team — preserved as-is)
    State-based pipeline agent.  Reads state.review_decisions (row-level
    ReviewDecision) and writes to state.approved_transformations / state.audit_log.
    Drives the orchestrator and FastAPI layer.

Agent4 (Member 3 integration)
    Field-mapping transformation engine.  Operates on ReviewRecommendation /
    FieldReviewDecision pairs and returns a TransformationResult.  Includes
    the Normalizer for deterministic value cleaning.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.review_models import (
    DecisionType,
    FieldReviewDecision,
    ReviewRecommendation,
)
from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.transformation_models import Transformation
from app.models.audit_models import AuditEntry
from app.services.excel_service import ExcelService


# ---------------------------------------------------------------------------
# Team class — preserved and connected to M3 transformations & excel output
# ---------------------------------------------------------------------------

class ControlledTransformationAgent:
    """
    Agent 4: Safely executes approved data corrections and produces the final cleaned SOV.
    """

    def __init__(self):
        pass

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute controlled transformations based on human review decisions.

        Rules:
        - PENDING → no transformation applied
        - ACCEPT / approve → apply proposed recommendation
        - EDIT → apply human-edited value
        - REJECT → no transformation, record showing before == after
        - No automatic approval.

        Args:
            state (SOVProcessingState): Pipeline state containing review_decisions and recommendations.

        Returns:
            SOVProcessingState: Updated state with approved_transformations, audit_log, and final_output_path.
        """
        state.status = JobStatus.TRANSFORMING

        # Build lookup maps for recommendations
        rec_map = {(r.row, r.field): r for r in state.recommendations}
        rec_by_field = {r.field: r for r in state.recommendations}

        # Track rows for generating Cleaned_SOV.xlsx
        rows_data: dict[int, dict[str, Any]] = {}
        if "source_rows" in state.metadata and isinstance(state.metadata["source_rows"], list):
            for idx, r in enumerate(state.metadata["source_rows"], start=1):
                rows_data[idx] = copy.deepcopy(r)
        else:
            for rec in state.recommendations:
                if rec.row not in rows_data:
                    rows_data[rec.row] = {"Reference": f"LOC-{rec.row:03d}"}
                rows_data[rec.row][rec.field] = rec.current_value

        for decision in state.review_decisions:
            dec_raw = decision.decision.value if hasattr(decision.decision, "value") else str(decision.decision)
            dec_type = dec_raw.lower()

            rec = rec_map.get((decision.row, decision.field)) or rec_by_field.get(decision.field)
            raw_before = getattr(rec, "current_value", None) if rec else "RAW_VALUE"
            confidence = getattr(rec, "confidence", 1.0) if rec else 1.0
            reviewer = getattr(decision, "reviewer", None) or getattr(decision, "approver", "human_reviewer")

            if dec_type in ("approve", "accept"):
                if rec is not None:
                    target_value = getattr(rec, "proposed_value", None)
                    if target_value is None:
                        target_value = getattr(rec, "recommendation", None)
                    if target_value is None:
                        target_value = "TRANSFORMED_VALUE"
                else:
                    target_value = "TRANSFORMED_VALUE"

                transformation = Transformation(
                    row=decision.row,
                    field=decision.field,
                    before=raw_before,
                    after=target_value,
                    transformation=f"applied_{dec_type}",
                    approved_by=reviewer,
                    approved_at=datetime.now(timezone.utc),
                )
                state.approved_transformations.append(transformation)

                audit_record = AuditEntry(
                    job_id=state.job_id,
                    user_id=reviewer,
                    action=f"applied_transformation_{dec_type}",
                    source=f"Row {decision.row}, {decision.field}",
                    target=decision.field,
                    before=raw_before,
                    after=target_value,
                    confidence=confidence,
                    approver=reviewer,
                    timestamp=datetime.now(timezone.utc),
                )
                state.audit_log.append(audit_record)

                if decision.row not in rows_data:
                    rows_data[decision.row] = {"Reference": f"LOC-{decision.row:03d}"}
                rows_data[decision.row][decision.field] = target_value

            elif dec_type in ("edit",):
                target_value = decision.edited_value
                transformation = Transformation(
                    row=decision.row,
                    field=decision.field,
                    before=raw_before,
                    after=target_value,
                    transformation="applied_edit",
                    approved_by=reviewer,
                    approved_at=datetime.now(timezone.utc),
                )
                state.approved_transformations.append(transformation)

                audit_record = AuditEntry(
                    job_id=state.job_id,
                    user_id=reviewer,
                    action="applied_transformation_edit",
                    source=f"Row {decision.row}, {decision.field}",
                    target=decision.field,
                    before=raw_before,
                    after=target_value,
                    confidence=confidence,
                    approver=reviewer,
                    timestamp=datetime.now(timezone.utc),
                )
                state.audit_log.append(audit_record)

                if decision.row not in rows_data:
                    rows_data[decision.row] = {"Reference": f"LOC-{decision.row:03d}"}
                rows_data[decision.row][decision.field] = target_value

            elif dec_type in ("reject",):
                # REJECT → No transformation applied; auditable record where before == after
                audit_record = AuditEntry(
                    job_id=state.job_id,
                    user_id=reviewer,
                    action="recommendation_rejected",
                    source=f"Row {decision.row}, {decision.field}",
                    target=decision.field,
                    before=raw_before,
                    after=raw_before,
                    confidence=confidence,
                    approver=reviewer,
                    timestamp=datetime.now(timezone.utc),
                )
                state.audit_log.append(audit_record)
                if decision.row not in rows_data:
                    rows_data[decision.row] = {"Reference": f"LOC-{decision.row:03d}"}
                rows_data[decision.row][decision.field] = raw_before

        # Any recommendation without a decision remains PENDING (untouched, no audit acceptance)

        # Generate Cleaned_SOV.xlsx
        excel_service = ExcelService()
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"cleaned_sov_{state.job_id}.xlsx"

        final_records = [rows_data[r] for r in sorted(rows_data.keys())] if rows_data else [{"Reference": "LOC-001"}]
        resolved_path = excel_service.write(records=final_records, output_path=output_file)

        state.final_output_path = str(resolved_path)
        state.status = JobStatus.COMPLETED
        return state


# ---------------------------------------------------------------------------
# Member 3 integration — field-mapping transformation engine
# ---------------------------------------------------------------------------

# State abbreviation map — extend as needed
_STATE_MAP: Dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC",
}


class Normalizer:
    """
    Applies simple, deterministic value transformations.

    All methods are static — no state is held.
    No LLM is used. No guessing. Only explicit, predictable rules.

    Supported transformations
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    - Currency strings → float   e.g. "$1,250,000" → 1250000.0
    - Sprinkler flags  → "Y"/"N" e.g. "YES" / "yes" → "Y"
    - US state names   → abbrev  e.g. "Massachusetts" → "MA"
    """

    @staticmethod
    def normalize_currency(value: Any) -> float:
        """
        Strip currency symbols, commas, and whitespace then convert to float.

        Examples
        --------
        "$1,250,000"   → 1250000.0
        "$500,000.50"  → 500000.5
        "1250000"      → 1250000.0
        1250000        → 1250000.0   (already numeric)

        Raises
        ------
        ValueError  if the value cannot be interpreted as a number.
        """
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r"[\$,\s]", "", str(value))
        try:
            return float(cleaned)
        except ValueError:
            raise ValueError(
                f"Cannot convert '{value}' to a numeric currency value."
            )

    @staticmethod
    def normalize_sprinkler(value: Any) -> str:
        """
        Normalise yes/no sprinkler flags to "Y" or "N".

        Examples
        --------
        "YES" / "Yes" / "yes" → "Y"
        "NO"  / "No"  / "no"  → "N"
        "Y"                   → "Y"
        "N"                   → "N"

        Raises
        ------
        ValueError  if the value is not a recognised yes/no variant.
        """
        mapping = {
            "yes": "Y", "y": "Y",
            "no":  "N", "n": "N",
        }
        normalised = mapping.get(str(value).strip().lower())
        if normalised is None:
            raise ValueError(
                f"Cannot normalise '{value}' to a sprinkler flag (expected YES/NO/Y/N)."
            )
        return normalised

    @staticmethod
    def normalize_state(value: Any) -> str:
        """
        Convert a US state full name to its two-letter abbreviation.

        Already-abbreviated values (len == 2) are returned uppercased as-is.

        Examples
        --------
        "Massachusetts" → "MA"
        "new york"      → "NY"
        "TX"            → "TX"

        Raises
        ------
        ValueError  if the state name is not recognised.
        """
        text = str(value).strip()
        if len(text) == 2:
            return text.upper()
        abbrev = _STATE_MAP.get(text.lower())
        if abbrev is None:
            raise ValueError(
                f"Cannot normalise '{value}' to a US state abbreviation."
            )
        return abbrev


@dataclass
class TransformationResult:
    """
    Lightweight result object returned by Agent4.transform().

    Attributes
    ----------
    transformed_data      : The new dict/row after approved transformations.
    applied_count         : Number of ACCEPT decisions applied.
    edited_count          : Number of EDIT decisions applied.
    rejected_count        : Number of REJECT decisions skipped.
    pending_count         : Number of items with no decision (skipped).
    """

    transformed_data: Dict[str, Any]
    applied_count:    int = 0   # ACCEPT
    edited_count:     int = 0   # EDIT
    rejected_count:   int = 0   # REJECT
    pending_count:    int = 0   # no decision yet

    @property
    def total_skipped(self) -> int:
        """Decisions that did NOT result in a change (REJECT + PENDING)."""
        return self.rejected_count + self.pending_count


class Agent4:
    """
    Controlled Transformation component (Member 3 integration).

    Operates on ReviewRecommendation / FieldReviewDecision pairs produced by
    HumanReview and returns a TransformationResult.

    Usage
    ~~~~~
        agent = Agent4()

        result = agent.transform(
            source_row={"Bldg Repl Cost": "$1,250,000"},
            recommendations=[rec1, rec2],
            decisions=[decision1, decision2],
        )

        print(result.transformed_data)   # {"Building Value": 1250000.0}
        print(result.applied_count)      # 1
        print(result.rejected_count)     # 0
        print(result.pending_count)      # 1

    Decision rules
    ~~~~~~~~~~~~~~
    - ACCEPT  → apply the AI recommendation value (normalised).
    - EDIT    → apply the human-supplied edited_value (normalised).
    - REJECT  → leave the field untouched.
    - None    → PENDING; leave the field untouched; never auto-approve.

    Validation
    ~~~~~~~~~~
    Each FieldReviewDecision is matched to its ReviewRecommendation by
    (source_field, target_field).  A mismatch raises ValueError immediately —
    Agent4 never silently applies a decision to the wrong field.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transform(
        self,
        source_row: Dict[str, Any],
        recommendations: List[ReviewRecommendation],
        decisions: List[Optional[FieldReviewDecision]],
    ) -> TransformationResult:
        """
        Apply human-approved decisions to a single SOV row (dict).

        Parameters
        ----------
        source_row      : Original SOV row as a plain dict. NOT modified.
        recommendations : List of AI ReviewRecommendations (one per field).
        decisions       : Matching list of FieldReviewDecisions (or None = PENDING).
                          Must be the same length as recommendations.

        Returns
        -------
        TransformationResult

        Raises
        ------
        ValueError   if recommendations and decisions differ in length.
        ValueError   if a decision's (source_field, target_field) doesn't
                     match its paired ReviewRecommendation.
        """
        if len(recommendations) != len(decisions):
            raise ValueError(
                f"recommendations and decisions must have the same length. "
                f"Got {len(recommendations)} recommendations and "
                f"{len(decisions)} decisions."
            )

        # Work on a copy — never touch the original
        transformed: Dict[str, Any] = copy.deepcopy(source_row)

        applied_count  = 0
        edited_count   = 0
        rejected_count = 0
        pending_count  = 0

        for rec, decision in zip(recommendations, decisions):
            # ── PENDING: no decision provided ──────────────────────────
            if decision is None:
                pending_count += 1
                continue

            # ── Validate field matching ─────────────────────────────────
            self._validate_match(rec, decision)

            # ── REJECT: skip without applying anything ──────────────────
            if decision.decision == DecisionType.REJECT:
                rejected_count += 1
                continue

            # ── ACCEPT: use the recommendation value ────────────────────
            if decision.decision == DecisionType.ACCEPT:
                value = self._resolve_value(rec.recommendation, rec.target_field)
                transformed[rec.target_field] = value
                applied_count += 1

            # ── EDIT: use the human's edited_value ──────────────────────
            elif decision.decision == DecisionType.EDIT:
                value = self._resolve_value(decision.edited_value, rec.target_field)
                transformed[rec.target_field] = value
                edited_count += 1

        return TransformationResult(
            transformed_data=transformed,
            applied_count=applied_count,
            edited_count=edited_count,
            rejected_count=rejected_count,
            pending_count=pending_count,
        )

    # ------------------------------------------------------------------
    # Batch convenience
    # ------------------------------------------------------------------

    def transform_batch(
        self,
        source_rows: List[Dict[str, Any]],
        recommendations_per_row: List[List[ReviewRecommendation]],
        decisions_per_row: List[List[Optional[FieldReviewDecision]]],
    ) -> List[TransformationResult]:
        """
        Apply transformations to multiple SOV rows.

        Each element in source_rows maps to the corresponding element in
        recommendations_per_row and decisions_per_row.

        Returns a list of TransformationResult, one per row.
        """
        if not (
            len(source_rows)
            == len(recommendations_per_row)
            == len(decisions_per_row)
        ):
            raise ValueError(
                "source_rows, recommendations_per_row, and decisions_per_row "
                "must all have the same length."
            )
        return [
            self.transform(row, recs, decs)
            for row, recs, decs in zip(
                source_rows, recommendations_per_row, decisions_per_row
            )
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_match(
        rec: ReviewRecommendation, decision: FieldReviewDecision
    ) -> None:
        """
        Raise ValueError if the decision doesn't correspond to the recommendation.

        Checks both source_field and target_field — both must match.
        """
        if (
            rec.source_field != decision.source_field
            or rec.target_field != decision.target_field
        ):
            raise ValueError(
                f"Decision field mismatch.\n"
                f"  Recommendation : source='{rec.source_field}' "
                f"target='{rec.target_field}'\n"
                f"  Decision       : source='{decision.source_field}' "
                f"target='{decision.target_field}'"
            )

    @staticmethod
    def _resolve_value(value: Any, target_field: str) -> Any:
        """
        Apply deterministic normalizations based on the target field name.

        Rules are keyed on the target_field string (case-insensitive substrings):
          - "value" / "cost" / "amount" / "tiv"  → currency normalization
          - "sprinkler"                            → Y/N normalization
          - "state"                               → state abbreviation

        If no rule matches, the raw value is returned as-is.
        """
        if value is None:
            return value

        field_lower = target_field.lower()

        # Currency fields
        if any(kw in field_lower for kw in ("value", "cost", "amount", "tiv")):
            try:
                return Normalizer.normalize_currency(value)
            except ValueError:
                # Not numeric — return raw (e.g. "N/A", "TBD")
                return value

        # Sprinkler / fire protection
        if "sprinkler" in field_lower:
            try:
                return Normalizer.normalize_sprinkler(value)
            except ValueError:
                return value

        # US state fields
        if "state" in field_lower:
            try:
                return Normalizer.normalize_state(value)
            except ValueError:
                return value

        # No normalization rule — return raw value
        return value

