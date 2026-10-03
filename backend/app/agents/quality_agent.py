"""Agent 3: Data Quality & Reasoning Agent

Responsible for:
- Scanning the mapped tabular SOV data for data anomalies and rule violations against
  the 17 canonical SOV fields.
- Identifying missing mandatory fields, invalid values, negative monetary values,
  non-integer fields, invalid fire sprinkler indicators, invalid state/country representations,
  and duplicate records.
- Providing controlled contextual reasoning via Qwen for ambiguous/non-standard textual fields
  (e.g. Occupancy, Construction).
- Enforcing deterministic human-review routing policies:
    PASS   -> continue automatically
    LOW    -> log only (no human review required)
    MEDIUM -> human review required
    HIGH   -> human review required
- Generating actionable recommendations with human-review guidance.

Authoritative Canonical Schema (17 Fields):
1. Reference (String)
2. Address (String)
3. City (String)
4. State (String)
5. Zip (Integer)
6. County (String)
7. Country (String)
8. Building Value (Float)
9. Contents (Float)
10. BI (Float)
11. Occupancy (String)
12. Construction (String)
13. Storeys (Integer)
14. Number of Buildings (Integer)
15. Year Built (Integer)
16. Fire Sprinklers (Y/N) (String) - Allowed: Y, N, Y13, Y(13R)
17. Other (Float)

Schema Conformance & Safety Rules:
- Legacy fields (Location Name, Contents Value, Total Insured Value, Square Footage,
  Number of Stories) MUST NOT be used or substituted.
- No historical thresholds (no Building Value > X or < X anomaly checks).
- Zero is allowed for monetary fields; zero Building Value is not treated as invalid
  solely because it is zero.
- No invented cross-field rules (no Contents < Building Value or sum checks).
- Values violating types are flagged with recommendations to verify against source records;
  Agent 3 never silently converts or replaces source values (proposed_value is always None).
- Qwen is advisory only: cannot modify SOV, cannot invent replacement values, cannot decide routing.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.quality_models import (
    QualityIssue,
    QualityReport,
    Recommendation,
    IssueType,
    IssueSeverity,
)

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical 17 SOV Fields (Authoritative Order)
# ---------------------------------------------------------------------------

CANONICAL_SOV_FIELDS: list[str] = [
    "Reference",
    "Address",
    "City",
    "State",
    "Zip",
    "County",
    "Country",
    "Building Value",
    "Contents",
    "BI",
    "Occupancy",
    "Construction",
    "Storeys",
    "Number of Buildings",
    "Year Built",
    "Fire Sprinklers (Y/N)",
    "Other",
]

_SOV_FIELD_NAMES = CANONICAL_SOV_FIELDS

# Fields where missing value is a critical/high severity issue
_REQUIRED_FIELDS: set[str] = {
    "Reference",
    "Address",
    "City",
    "State",
    "Building Value",
}

# Float monetary fields (zero is allowed; negative values are invalid)
_FLOAT_FIELDS: list[str] = [
    "Building Value",
    "Contents",
    "BI",
    "Other",
]

# Integer fields (must be whole numbers, non-negative)
_INTEGER_FIELDS: list[str] = [
    "Storeys",
    "Number of Buildings",
]

# Authoritative allowed sprinkler values
_VALID_SPRINKLER_VALUES: set[str] = {
    "Y",
    "N",
    "Y13",
    "Y(13R)",
}

# Configured Year Built boundaries
_CURRENT_YEAR = datetime.now().year
_MIN_YEAR_BUILT = 1700
_MAX_YEAR_BUILT = _CURRENT_YEAR + 2

# Configured valid US state abbreviations
_VALID_US_STATES: set[str] = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "GU", "VI", "AS", "MP",  # territories
}

# Configured valid Country representations
_VALID_COUNTRIES: set[str] = {
    "US", "USA", "UNITED STATES", "UNITED STATES OF AMERICA",
    "CA", "CAN", "CANADA", "GB", "GBR", "UK", "UNITED KINGDOM",
    "AU", "AUS", "AUSTRALIA", "MX", "MEX", "MEXICO",
}

# Recognized standard occupancy terms (exact/substring lookup to avoid unnecessary LLM calls)
_STANDARD_OCCUPANCIES: set[str] = {
    "OFFICE", "RESIDENTIAL", "COMMERCIAL", "RETAIL", "INDUSTRIAL",
    "WAREHOUSE", "MANUFACTURING", "HOSPITAL", "HEALTHCARE", "HOTEL",
    "MOTEL", "RESTAURANT", "SCHOOL", "EDUCATION", "APARTMENT",
    "MULTI-FAMILY", "SINGLE FAMILY", "CHURCH", "RELIGIOUS", "VACANT",
    "STORAGE", "AGRICULTURE", "FARM",
}

# Recognized standard construction materials/types
_STANDARD_CONSTRUCTIONS: set[str] = {
    "FRAME", "JOISTED MASONRY", "NON-COMBUSTIBLE", "MASONRY NON-COMBUSTIBLE",
    "MODIFIED FIRE RESISTIVE", "FIRE RESISTIVE", "WOOD", "WOOD FRAME",
    "STEEL", "STRUCTURAL STEEL", "CONCRETE", "REINFORCED CONCRETE",
    "MASONRY", "BRICK", "METAL", "PRE-ENGINEERED METAL", "HEAVY TIMBER",
}


# ---------------------------------------------------------------------------
# Human-Review Routing Policy (Deterministic)
# ---------------------------------------------------------------------------

def requires_human_review(severity: str) -> bool:
    """
    Deterministic human-review routing policy:
    PASS   -> continue automatically (no issue)
    LOW    -> log only (requires_human_review = False)
    MEDIUM -> human review (requires_human_review = True)
    HIGH   -> human review (requires_human_review = True)
    """
    sev = str(severity).lower()
    return sev in {"medium", "high", "critical", "error", "warning"}


# ---------------------------------------------------------------------------
# Qwen Contextual Reasoning System Prompt & Structured Output
# ---------------------------------------------------------------------------

_QWEN_QUALITY_SYSTEM_PROMPT = """You are assisting an insurance SOV data-quality agent.
You are a reasoning assistant, not a data transformation agent.
The canonical schema has exactly 17 fields.
Never invent missing data.
Never infer a replacement value.
Never modify the supplied SOV.
Never map TIV to Building Value.
Geographic values are not financial values.
Quantity/count fields are not monetary values.
Construction/material is not a monetary value.
Only reason about the supplied value and its context.
If evidence is insufficient, say so.
Return JSON only.
Severity must be low, medium, or high.
Recommendation must tell the human what to verify, not what value to insert.

Your output must be a valid JSON object with exactly these keys:
{
  "severity": "low|medium|high",
  "reasoning": "Human-readable explanation of why this value is ambiguous or non-standard.",
  "recommendation": "What a human reviewer should verify against the original source document."
}"""


class QwenQualityOutput(BaseModel):
    """Structured response from Qwen contextual reasoning."""

    severity: str = Field(..., description="Suggested severity: low, medium, or high")
    reasoning: str = Field(..., description="Human-readable explanation")
    recommendation: str = Field(..., description="What a human should verify")


def _parse_qwen_quality_response(content: str) -> Optional[QwenQualityOutput]:
    """Parse and validate JSON response from Qwen."""
    if not content:
        return None
    try:
        # Strip markdown fences if present
        raw = content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        if not isinstance(data, dict):
            return None

        sev = str(data.get("severity", "")).lower().strip()
        if sev not in {"low", "medium", "high"}:
            return None

        reasoning = str(data.get("reasoning", "")).strip()
        recommendation = str(data.get("recommendation", "")).strip()
        if not reasoning or not recommendation:
            return None

        return QwenQualityOutput(
            severity=sev,
            reasoning=reasoning,
            recommendation=recommendation,
        )
    except Exception as e:
        logger.warning(f"Failed to parse Qwen quality response: {e}")
        return None


def _build_qwen_quality_user_prompt(
    field: str,
    value: Any,
    row_idx: int,
    row_context: dict[str, Any],
) -> str:
    """Build user prompt for Qwen contextual reasoning."""
    context_str = json.dumps(
        {k: v for k, v in row_context.items() if k in CANONICAL_SOV_FIELDS and v is not None},
        indent=2,
        default=str,
    )
    return f"""Evaluate the following non-standard or ambiguous SOV value in an insurance property underwriting context.

Field: {field}
Value to evaluate: {value}
Row: {row_idx}

Row context:
{context_str}

Analyze whether this value represents a plausible or non-standard {field} description.
Remember:
- Do NOT invent or infer a replacement value.
- Severity must be low, medium, or high.
- Tell the human reviewer what source records to verify."""


class QwenQualityAdapter:
    """
    Configurable, mockable adapter for Qwen contextual reasoning.
    Supports injected callables (for tests/mocks) and real DashScope/OpenAI cloud integration.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        llm_callable: Optional[Callable[[dict[str, Any]], Optional[dict[str, Any]]]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        http_client: Optional[Any] = None,
    ):
        self.model_name = model_name or os.getenv("SOV_LLM_MODEL", "qwen3.7-plus")
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = (
            base_url
            or os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        ).rstrip("/")
        self.timeout_sec = float(timeout or os.getenv("SOV_LLM_TIMEOUT", "15.0"))
        self.http_client = http_client
        self.llm_callable = llm_callable

    def reason(
        self,
        field: str,
        value: Any,
        row_idx: int,
        row_context: dict[str, Any],
    ) -> Optional[QwenQualityOutput]:
        """
        Invoke Qwen contextual reasoning. Fails safely and returns None on error/timeout.
        """
        payload = {
            "field": field,
            "value": value,
            "row": row_idx,
            "row_context": row_context,
        }

        # If custom callable is injected (for tests/mocks)
        if self.llm_callable is not None:
            try:
                res = self.llm_callable(payload)
                if res is None:
                    return None
                if isinstance(res, dict):
                    content = json.dumps(res)
                    return _parse_qwen_quality_response(content)
                return _parse_qwen_quality_response(str(res))
            except Exception as e:
                logger.warning(f"Injected Qwen callable error: {e}")
                return None

        # Cloud API call via DashScope
        if not self.api_key:
            logger.debug("DASHSCOPE_API_KEY not configured; skipping Qwen reasoning call.")
            return None

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        user_prompt = _build_qwen_quality_user_prompt(field, value, row_idx, row_context)
        request_body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": _QWEN_QUALITY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        try:
            if self.http_client is not None:
                resp = self.http_client.post(
                    endpoint, headers=headers, json=request_body, timeout=self.timeout_sec
                )
            else:
                import httpx
                with httpx.Client(timeout=self.timeout_sec) as client:
                    resp = client.post(endpoint, headers=headers, json=request_body)

            if resp.status_code != 200:
                logger.warning(f"Qwen API returned status {resp.status_code}: {resp.text}")
                return None

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                logger.warning("Qwen API returned empty choices.")
                return None

            content = choices[0].get("message", {}).get("content", "")
            return _parse_qwen_quality_response(content)

        except Exception as e:
            logger.warning(f"Qwen API contextual reasoning call error: {e}")
            return None


def should_invoke_qwen(field: str, value: Any) -> bool:
    """
    Explicit Qwen routing check:
    Determines whether contextual interpretation is genuinely useful.
    Deterministic issues (missing values, invalid numeric values, negative values,
    unsupported sprinklers, invalid state codes, valid clean rows) do NOT call Qwen.
    Qwen is only considered for ambiguous/non-standard textual descriptions in fields
    such as Occupancy and Construction.
    """
    if _is_empty(value):
        return False

    val_str = str(value).strip().upper()

    if field == "Occupancy":
        # Pure numeric values are handled deterministically as invalid
        ok, _ = _to_float(val_str)
        if ok and not re.search(r"[a-zA-Z]", val_str):
            return False
        # If matches exact standard recognized occupancy, it's clean (no Qwen)
        if val_str in _STANDARD_OCCUPANCIES:
            return False
        return True

    if field == "Construction":
        # Monetary/numeric values are handled deterministically
        if val_str.startswith("$") or (re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?$", val_str) and not re.search(r"[a-zA-Z]", val_str)):
            return False
        # If matches exact standard recognized construction, it's clean (no Qwen)
        if val_str in _STANDARD_CONSTRUCTIONS:
            return False
        return True

    return False


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _to_float(value: Any) -> tuple[bool, Optional[float]]:
    if value is None:
        return False, None
    try:
        cleaned = str(value).replace(",", "").replace("$", "").strip()
        # Handle accounting negative parenthesized numbers e.g. "(500)"
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        return True, float(cleaned)
    except (ValueError, TypeError):
        return False, None


def _to_int(value: Any) -> tuple[bool, Optional[int]]:
    ok, fval = _to_float(value)
    if not ok or fval is None:
        return False, None
    return True, int(fval)


def _normalise_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _make_issue(
    row: int,
    field: str,
    issue: str,
    severity: str,
    current_value: Any,
    recommendation: Optional[str] = None,
    confidence: float = 1.0,
    reasoning: str = "",
    issue_type: Optional[str] = None,
    reasoning_source: str = "deterministic",
    qwen_used: bool = False,
    proposed_value: Any = None,
) -> QualityIssue:
    """Construct a QualityIssue with complete human-review metadata."""
    return QualityIssue(
        row=row,
        field=field,
        issue=issue,
        severity=severity,
        current_value=current_value,
        value=current_value,
        recommendation=recommendation or issue,
        confidence=confidence,
        reasoning=reasoning or issue,
        issue_type=issue_type,
        requires_human_review=requires_human_review(severity),
        reasoning_source=reasoning_source,
        qwen_used=qwen_used,
        proposed_value=proposed_value,
    )


# ---------------------------------------------------------------------------
# Individual deterministic check functions (Strictly 17 Canonical Fields)
# ---------------------------------------------------------------------------

def _check_missing_values(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """Flag missing mandatory or expected values in canonical fields."""
    for row_idx, row in enumerate(rows, start=1):
        for field in CANONICAL_SOV_FIELDS:
            if field not in row:
                continue
            value = row.get(field)
            if _is_empty(value):
                is_required = field in _REQUIRED_FIELDS
                if is_required:
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field=field,
                            issue=f"Field '{field}' is required but has no value.",
                            severity=IssueSeverity.high.value,
                            current_value=value,
                            recommendation="Check the source document for the missing value.",
                            reasoning=f"Field '{field}' is required for underwriting but has no value in row {row_idx}.",
                            issue_type=IssueType.missing_value.value,
                            reasoning_source="deterministic",
                        )
                    )
                elif field == "County":
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field=field,
                            issue="Field 'County' is empty.",
                            severity=IssueSeverity.low.value,
                            current_value=value,
                            recommendation="Provide County from source records if available; do not infer from City, State, or Zip.",
                            reasoning=f"County is missing in row {row_idx}.",
                            issue_type=IssueType.missing_value.value,
                            reasoning_source="deterministic",
                        )
                    )
                else:
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field=field,
                            issue=f"Field '{field}' has no value.",
                            severity=IssueSeverity.medium.value,
                            current_value=value,
                            recommendation="Check the source document for the missing value.",
                            reasoning=f"Field '{field}' is optional but empty in row {row_idx}.",
                            issue_type=IssueType.missing_value.value,
                            reasoning_source="deterministic",
                        )
                    )


def _check_invalid_numerics(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """
    Validate Float fields: Building Value, Contents, BI, Other.
    - Must be numeric when supplied.
    - Negative values are invalid.
    - Zero is allowed and must NOT automatically be treated as invalid.
    """
    for row_idx, row in enumerate(rows, start=1):
        for field in _FLOAT_FIELDS:
            if field not in row:
                continue
            value = row[field]
            if _is_empty(value):
                continue

            ok, num = _to_float(value)
            if not ok:
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"'{value}' in field '{field}' cannot be parsed as a numeric value.",
                        severity=IssueSeverity.high.value,
                        current_value=value,
                        recommendation="Verify the value against the original source document.",
                        reasoning=f"Field '{field}' requires a Float representation, but received '{value}'.",
                        issue_type=IssueType.invalid_numeric.value,
                        reasoning_source="deterministic",
                    )
                )
            elif num is not None and num < 0:
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"'{field}' has a negative value ({num:,.2f}), which is invalid.",
                        severity=IssueSeverity.high.value,
                        current_value=value,
                        recommendation="Verify the value against the original source document.",
                        reasoning=f"Field '{field}' cannot have a negative value ({num:,.2f}).",
                        issue_type=IssueType.invalid_numeric.value,
                        reasoning_source="deterministic",
                    )
                )


def _check_zip(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """
    Validate Zip code.
    - Must be valid integer postal code representation.
    - Negative values are invalid.
    - Preserves leading zeros when represented as strings.
    - Do not invent or infer ZIP from Address or City.
    """
    field = "Zip"
    for row_idx, row in enumerate(rows, start=1):
        if field not in row:
            continue
        value = row[field]
        if _is_empty(value):
            continue

        if isinstance(value, (int, float)):
            if value < 0:
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"Zip code cannot be negative ({value}).",
                        severity=IssueSeverity.high.value,
                        current_value=value,
                        recommendation="Verify the value against the original source document.",
                        reasoning=f"Postal codes cannot be negative numbers in row {row_idx}.",
                        issue_type=IssueType.invalid_value.value,
                        reasoning_source="deterministic",
                    )
                )
            continue

        val_str = str(value).strip()
        if not re.match(r"^\d{3,5}(-\d{4})?$", val_str):
            issues.append(
                _make_issue(
                    row=row_idx,
                    field=field,
                    issue=f"'{value}' in field 'Zip' is not a valid postal code format.",
                    severity=IssueSeverity.medium.value,
                    current_value=value,
                    recommendation="Verify the value against the original source document.",
                    reasoning=f"Postal code '{value}' in row {row_idx} is not a valid integer/postal code representation.",
                    issue_type=IssueType.invalid_value.value,
                    reasoning_source="deterministic",
                )
            )


def _check_invalid_integers(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """
    Validate Integer fields: Storeys, Number of Buildings.
    - Must be an integer when supplied.
    - Fractional values are invalid.
    - Negative values are invalid.
    """
    for row_idx, row in enumerate(rows, start=1):
        for field in _INTEGER_FIELDS:
            if field not in row:
                continue
            value = row[field]
            if _is_empty(value):
                continue

            ok, num = _to_float(value)
            if not ok or num is None:
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"'{value}' in field '{field}' cannot be parsed as an integer.",
                        severity=IssueSeverity.medium.value,
                        current_value=value,
                        recommendation="Verify the value against the original source document.",
                        reasoning=f"Field '{field}' requires an integer value.",
                        issue_type=IssueType.invalid_value.value,
                        reasoning_source="deterministic",
                    )
                )
            elif num < 0:
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"'{field}' has a negative value ({num}), which is invalid.",
                        severity=IssueSeverity.high.value,
                        current_value=value,
                        recommendation="Verify the value against the original source document.",
                        reasoning=f"Field '{field}' cannot be negative in row {row_idx}.",
                        issue_type=IssueType.invalid_value.value,
                        reasoning_source="deterministic",
                    )
                )
            elif num != int(num):
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"'{field}' should be an integer; got fractional value {value}.",
                        severity=IssueSeverity.low.value,
                        current_value=value,
                        recommendation="Verify the value against the original source document.",
                        reasoning=f"Field '{field}' cannot be fractional ({value}) in row {row_idx}.",
                        issue_type=IssueType.invalid_value.value,
                        reasoning_source="deterministic",
                    )
                )


def _check_year_built(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """Validate Year Built (must represent an integer year in configured range)."""
    field = "Year Built"
    for row_idx, row in enumerate(rows, start=1):
        if field not in row:
            continue
        value = row[field]
        if _is_empty(value):
            continue

        ok, num = _to_float(value)
        if not ok or num is None or num != int(num):
            issues.append(
                _make_issue(
                    row=row_idx,
                    field=field,
                    issue=f"'{value}' cannot be interpreted as an integer year.",
                    severity=IssueSeverity.medium.value,
                    current_value=value,
                    recommendation="Verify Year Built against the original source document.",
                    reasoning=f"Year Built must be an integer year, but got '{value}' in row {row_idx}.",
                    issue_type=IssueType.invalid_year.value,
                    reasoning_source="deterministic",
                )
            )
        else:
            year = int(num)
            if year < _MIN_YEAR_BUILT or year > _MAX_YEAR_BUILT:
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=(
                            f"Year Built ({year}) is outside the accepted range "
                            f"[{_MIN_YEAR_BUILT}-{_MAX_YEAR_BUILT}]."
                        ),
                        severity=IssueSeverity.medium.value,
                        current_value=value,
                        recommendation="Verify Year Built against the original source document.",
                        reasoning=(
                            f"Year Built ({year}) in row {row_idx} is outside the configured "
                            f"valid year range [{_MIN_YEAR_BUILT}-{_MAX_YEAR_BUILT}]."
                        ),
                        issue_type=IssueType.invalid_year.value,
                        reasoning_source="deterministic",
                    )
                )


def _check_fire_sprinklers(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """Validate Fire Sprinklers (Y/N) against supported values: Y, N, Y13, Y(13R)."""
    field = "Fire Sprinklers (Y/N)"
    for row_idx, row in enumerate(rows, start=1):
        if field not in row:
            continue
        value = row[field]
        if _is_empty(value):
            continue

        norm = str(value).strip().upper()
        norm_compact = norm.replace(" ", "")
        if norm not in _VALID_SPRINKLER_VALUES and norm_compact not in _VALID_SPRINKLER_VALUES:
            issues.append(
                _make_issue(
                    row=row_idx,
                    field=field,
                    issue=f"'{value}' is not an allowed fire sprinkler indicator.",
                    severity=IssueSeverity.medium.value,
                    current_value=value,
                    recommendation="Verify Fire Sprinklers (Y/N) against the original source document and use a supported value.",
                    reasoning=(
                        f"'{value}' is outside the supported sprinkler values "
                        f"({', '.join(sorted(_VALID_SPRINKLER_VALUES))}) in row {row_idx}."
                    ),
                    issue_type=IssueType.invalid_sprinkler.value,
                    reasoning_source="deterministic",
                )
            )


def _check_state_country(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """Validate State and Country against configured valid representations."""
    for row_idx, row in enumerate(rows, start=1):
        # State
        if "State" in row:
            value = row["State"]
            if not _is_empty(value):
                norm = _normalise_str(value)
                if len(norm) != 2 or norm not in _VALID_US_STATES:
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field="State",
                            issue=f"'{value}' is not a recognised 2-letter US state code.",
                            severity=IssueSeverity.medium.value,
                            current_value=value,
                            recommendation="Verify the value against the original source document.",
                            reasoning=f"State '{value}' in row {row_idx} is not in the configured valid state representations.",
                            issue_type=IssueType.inconsistent_value.value,
                            reasoning_source="deterministic",
                        )
                    )

        # Country
        if "Country" in row:
            value = row["Country"]
            if not _is_empty(value):
                norm = _normalise_str(value)
                if norm not in _VALID_COUNTRIES:
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field="Country",
                            issue=f"'{value}' is not in the configured supported country representations.",
                            severity=IssueSeverity.low.value,
                            current_value=value,
                            recommendation="Verify the value against the original source document.",
                            reasoning=f"Country '{value}' in row {row_idx} is not in the supported country list.",
                            issue_type=IssueType.inconsistent_value.value,
                            reasoning_source="deterministic",
                        )
                    )


def _check_deterministic_occupancy_construction(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """Deterministic check for purely numeric/monetary format errors in Occupancy and Construction."""
    for row_idx, row in enumerate(rows, start=1):
        # Occupancy
        if "Occupancy" in row:
            val = row["Occupancy"]
            if not _is_empty(val):
                val_str = str(val).strip()
                ok, _ = _to_float(val_str)
                if ok and not re.search(r"[a-zA-Z]", val_str):
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field="Occupancy",
                            issue=f"'{val}' in Occupancy is purely numeric and does not describe building use.",
                            severity=IssueSeverity.medium.value,
                            current_value=val,
                            recommendation="Verify the value against the original source document.",
                            reasoning=f"Occupancy in row {row_idx} must describe building use (e.g. Residential, Office).",
                            issue_type=IssueType.invalid_value.value,
                            reasoning_source="deterministic",
                        )
                    )

        # Construction
        if "Construction" in row:
            val = row["Construction"]
            if not _is_empty(val):
                val_str = str(val).strip()
                if val_str.startswith("$") or (re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?$", val_str) and not re.search(r"[a-zA-Z]", val_str)):
                    issues.append(
                        _make_issue(
                            row=row_idx,
                            field="Construction",
                            issue=f"'{val}' in Construction appears to be a monetary or numeric value rather than a construction type.",
                            severity=IssueSeverity.medium.value,
                            current_value=val,
                            recommendation="Verify the value against the original source document.",
                            reasoning=f"Construction in row {row_idx} must represent construction type/material (e.g. Masonry, Steel, Wood).",
                            issue_type=IssueType.invalid_value.value,
                            reasoning_source="deterministic",
                        )
                    )


def _check_duplicates(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
) -> None:
    """Detect duplicate records using Exact, Normalized, and Fuzzy approaches."""
    from rapidfuzz import fuzz

    def _normalize_address(addr: str) -> str:
        if not addr:
            return ""
        norm = re.sub(r"[^\w\s]", " ", str(addr).lower())
        norm = re.sub(r"\s+", " ", norm).strip()
        replacements = {
            r"\bst\b": "street", r"\brd\b": "road", r"\bave\b": "avenue",
            r"\bblvd\b": "boulevard", r"\bln\b": "lane", r"\bdr\b": "drive",
            r"\bct\b": "court", r"\bpl\b": "place", r"\bsq\b": "square",
            r"\bste\b": "suite", r"\bapt\b": "apartment",
        }
        for pat, rep in replacements.items():
            norm = re.sub(pat, rep, norm)
        return norm

    def _normalize_ref(ref: str) -> str:
        if not ref:
            return ""
        return re.sub(r"[^\w]", "", str(ref).lower())

    parsed_rows = []
    for row_idx, row in enumerate(rows, start=1):
        ref_raw = str(row.get("Reference", "")).strip()
        addr_raw = str(row.get("Address", "")).strip()

        if not ref_raw:
            continue

        parsed_rows.append({
            "idx": row_idx,
            "ref_raw": ref_raw,
            "addr_raw": addr_raw,
            "ref_norm": _normalize_ref(ref_raw),
            "addr_norm": _normalize_address(addr_raw),
        })

    ref_groups: dict[str, list] = {}
    for pr in parsed_rows:
        ref_groups.setdefault(pr["ref_norm"], []).append(pr)

    for ref_norm, group in ref_groups.items():
        if len(group) < 2:
            continue

        flagged: set[int] = set()
        for i in range(len(group)):
            if group[i]["idx"] in flagged:
                continue
            for j in range(i + 1, len(group)):
                if group[j]["idx"] in flagged:
                    continue

                row_i, row_j = group[i], group[j]

                # LEVEL 1: Exact match
                if row_i["ref_raw"] == row_j["ref_raw"] and row_i["addr_raw"] == row_j["addr_raw"]:
                    issues.append(
                        _make_issue(
                            row=row_j["idx"],
                            field="Reference",
                            issue=f"Row {row_j['idx']} is an exact duplicate of row {row_i['idx']}.",
                            severity=IssueSeverity.high.value,
                            current_value=row_j["ref_raw"],
                            recommendation="Review source records to confirm whether these records represent the same property.",
                            reasoning=(
                                f"Row {row_j['idx']} is an exact duplicate of row {row_i['idx']} "
                                f"(Reference '{row_j['ref_raw']}' and Address '{row_j['addr_raw']}')."
                            ),
                            issue_type=IssueType.duplicate_record.value,
                            reasoning_source="deterministic",
                        )
                    )
                    flagged.add(row_j["idx"])
                    continue

                # LEVEL 2: Normalised address match
                if row_i["addr_norm"] == row_j["addr_norm"]:
                    issues.append(
                        _make_issue(
                            row=row_j["idx"],
                            field="Reference",
                            issue=f"Row {row_j['idx']} is a normalized duplicate of row {row_i['idx']}.",
                            severity=IssueSeverity.high.value,
                            current_value=row_j["ref_raw"],
                            recommendation="Review source records to confirm whether these records represent the same property.",
                            reasoning=(
                                f"Row {row_j['idx']} is a duplicate of row {row_i['idx']}. "
                                f"Their references and normalized addresses match "
                                f"(Address: '{row_j['addr_raw']}' vs '{row_i['addr_raw']}')."
                            ),
                            issue_type=IssueType.duplicate_record.value,
                            reasoning_source="deterministic",
                        )
                    )
                    flagged.add(row_j["idx"])
                    continue

                # LEVEL 3: Fuzzy match
                if not row_i["addr_norm"] or not row_j["addr_norm"]:
                    continue

                def _is_identifying_token(token: str) -> bool:
                    return bool(re.search(r"\d", token)) or len(token) <= 2

                def _has_meaningful_difference(a1: str, a2: str) -> bool:
                    c1 = re.sub(r"(?<=\d)(?=[a-zA-Z])|(?<=[a-zA-Z])(?=\d)", " ", a1)
                    c2 = re.sub(r"(?<=\d)(?=[a-zA-Z])|(?<=[a-zA-Z])(?=\d)", " ", a2)
                    tokens1, tokens2 = c1.split(), c2.split()
                    for t1 in tokens1:
                        if not _is_identifying_token(t1):
                            continue
                        if max([fuzz.ratio(t1, t2) for t2 in tokens2] + [0]) < 75.0:
                            return True
                    for t2 in tokens2:
                        if not _is_identifying_token(t2):
                            continue
                        if max([fuzz.ratio(t2, t1) for t1 in tokens1] + [0]) < 75.0:
                            return True
                    return False

                if _has_meaningful_difference(row_i["addr_norm"], row_j["addr_norm"]):
                    continue

                score = fuzz.ratio(row_i["addr_norm"], row_j["addr_norm"])
                if score >= 85.0:
                    issues.append(
                        _make_issue(
                            row=row_j["idx"],
                            field="Reference",
                            issue=f"Row {row_j['idx']} is a possible duplicate of row {row_i['idx']}.",
                            severity=IssueSeverity.medium.value,
                            current_value=row_j["ref_raw"],
                            recommendation="Review source records to confirm whether these records represent the same property.",
                            reasoning=(
                                f"Row {row_j['idx']} is a possible duplicate of row {row_i['idx']}. "
                                f"References match and addresses are highly similar "
                                f"('{row_j['addr_raw']}' vs '{row_i['addr_raw']}')."
                            ),
                            issue_type=IssueType.duplicate_record.value,
                            reasoning_source="deterministic",
                        )
                    )
                    flagged.add(row_j["idx"])


# ---------------------------------------------------------------------------
# Qwen Contextual Reasoning Layer
# ---------------------------------------------------------------------------

def _check_contextual_reasoning(
    rows: list[dict[str, Any]],
    issues: list[QualityIssue],
    llm_adapter: Optional[QwenQualityAdapter] = None,
) -> None:
    """
    Apply Qwen contextual reasoning ONLY for ambiguous/non-standard textual values
    where contextual interpretation is genuinely useful.
    Deterministic issues already handled are skipped.
    """
    candidate_fields = ["Occupancy", "Construction"]

    for row_idx, row in enumerate(rows, start=1):
        for field in candidate_fields:
            if field not in row:
                continue
            value = row.get(field)
            if not should_invoke_qwen(field, value):
                continue

            # Contextual reasoning is needed for this ambiguous field
            qwen_res: Optional[QwenQualityOutput] = None
            if llm_adapter is not None:
                qwen_res = llm_adapter.reason(
                    field=field,
                    value=value,
                    row_idx=row_idx,
                    row_context=row,
                )

            if qwen_res is not None:
                # Qwen reasoning succeeded
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"Ambiguous or non-standard '{field}' value requires review: '{value}'.",
                        severity=qwen_res.severity,
                        current_value=value,
                        recommendation=qwen_res.recommendation,
                        reasoning=qwen_res.reasoning,
                        confidence=0.85,
                        issue_type=IssueType.invalid_value.value,
                        reasoning_source="qwen",
                        qwen_used=True,
                        proposed_value=None,  # Qwen never invents replacement values
                    )
                )
            else:
                # Safe deterministic fallback when Qwen fails, times out, or is unavailable
                issues.append(
                    _make_issue(
                        row=row_idx,
                        field=field,
                        issue=f"Non-standard '{field}' value requires verification: '{value}'.",
                        severity=IssueSeverity.medium.value,
                        current_value=value,
                        recommendation=f"Verify {field} value against original source records.",
                        reasoning=f"Contextual reasoning unavailable for '{field}': '{value}'. Safe fallback applied.",
                        confidence=0.80,
                        issue_type=IssueType.invalid_value.value,
                        reasoning_source="qwen_fallback",
                        qwen_used=False,
                        proposed_value=None,  # Safe fallback never invents replacement values
                    )
                )


def _generate_recommendations(issues: list[QualityIssue]) -> list[Recommendation]:
    """
    Generate Recommendation objects from detected issues.
    Adheres strictly to TYPE SAFETY:
    - Agent 3 is a validator, not a transformation engine.
    - If a value violates expected type, reports the issue and recommends verification against source.
    - Does NOT silently convert, replace, guess, or invent values (proposed_value is always None).
    """
    recommendations: list[Recommendation] = []

    for issue in issues:
        action = f"verify_{issue.field.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}"

        if issue.issue_type == IssueType.duplicate_record.value:
            action = "reconcile_duplicate"
        elif issue.issue_type == IssueType.missing_value.value:
            action = f"supply_{issue.field.lower().replace(' ', '_')}"
        elif issue.issue_type == IssueType.invalid_numeric.value:
            action = f"verify_{issue.field.lower().replace(' ', '_')}"
        elif issue.issue_type == IssueType.invalid_sprinkler.value:
            action = "verify_sprinkler_status"
        elif issue.issue_type == IssueType.invalid_year.value:
            action = "verify_year_built"

        recommendations.append(
            Recommendation(
                row=issue.row,
                field=issue.field,
                action=action,
                current_value=issue.current_value,
                proposed_value=None,  # Do not invent, guess, or silently replace values
                confidence=issue.confidence,
                reasoning=issue.recommendation or issue.reasoning or issue.issue,
            )
        )

    return recommendations


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_quality(
    mapped_data: list[dict[str, Any]],
    llm_adapter: Optional[QwenQualityAdapter] = None,
) -> QualityReport:
    """
    Run all quality checks against *mapped_data* (list of canonical-keyed
    row dicts produced by Agent 2) strictly against the 17 canonical SOV fields.

    Flow:
      Agent 2 output
      -> deterministic validation
      -> determine whether contextual reasoning is actually needed
      -> Qwen only when needed (advisory only)
      -> combine result with configured routing policy
      -> produce QualityReport
      -> never modify the SOV data

    Returns a QualityReport. The input data is NEVER modified.
    """
    if not mapped_data:
        return QualityReport(
            total_rows_scanned=0,
            total_issues=0,
            issues=[],
            recommendations=[],
            summary={},
        )

    issues: list[QualityIssue] = []

    # Step 1: Deterministic validation across canonical fields
    _check_missing_values(mapped_data, issues)
    _check_invalid_numerics(mapped_data, issues)
    _check_zip(mapped_data, issues)
    _check_invalid_integers(mapped_data, issues)
    _check_year_built(mapped_data, issues)
    _check_fire_sprinklers(mapped_data, issues)
    _check_duplicates(mapped_data, issues)
    _check_state_country(mapped_data, issues)
    _check_deterministic_occupancy_construction(mapped_data, issues)

    # Step 2: Contextual reasoning layer (Qwen invoked only when needed)
    _check_contextual_reasoning(mapped_data, issues, llm_adapter=llm_adapter)

    # Sort: high severity first, then by row
    _severity_order = {
        IssueSeverity.high.value: 0,
        IssueSeverity.error.value: 0,
        IssueSeverity.critical.value: 0,
        IssueSeverity.medium.value: 1,
        IssueSeverity.warning.value: 1,
        IssueSeverity.low.value: 2,
        IssueSeverity.info.value: 2,
    }
    issues.sort(key=lambda i: (_severity_order.get(i.severity, 3), i.row))

    # Build summary counts by issue_type
    summary: dict[str, int] = {}
    for issue in issues:
        if issue.issue_type:
            summary[issue.issue_type] = summary.get(issue.issue_type, 0) + 1

    # Generate recommendations for human review
    recommendations = _generate_recommendations(issues)

    return QualityReport(
        total_rows_scanned=len(mapped_data),
        total_issues=len(issues),
        issues=issues,
        recommendations=recommendations,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# DataQualityAgent — shared pipeline interface
# ---------------------------------------------------------------------------

class DataQualityAgent:
    """
    Agent 3: Performs semantic and deterministic data quality inspection
    and proposes fixes for human review.

    Consumes mapped tabular data from state.metadata["mapped_rows"] (set by Agent 2)
    and populates state.quality_issues and state.recommendations.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        llm_adapter: Optional[QwenQualityAdapter] = None,
        llm_callable: Optional[Callable[[dict[str, Any]], Optional[dict[str, Any]]]] = None,
    ):
        self.model_name = model_name or os.getenv("SOV_LLM_MODEL", "qwen3.7-plus")
        if llm_adapter is not None:
            self.llm_adapter = llm_adapter
        elif llm_callable is not None:
            self.llm_adapter = QwenQualityAdapter(model_name=self.model_name, llm_callable=llm_callable)
        else:
            self.llm_adapter = QwenQualityAdapter(model_name=self.model_name)

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute data quality analysis and generate proposed recommendations.

        Reads from:
          state.metadata["mapped_rows"]  — canonical-keyed row dicts from Agent 2

        Writes to:
          state.quality_issues
          state.recommendations
          state.metadata["quality_report"]
        """
        mapped_rows: Optional[list[dict[str, Any]]] = state.metadata.get("mapped_rows")

        if not mapped_rows:
            # No mapped data available — log and set state without crashing
            logger.warning(
                "DataQualityAgent: No mapped_rows found in state.metadata. "
                "Ensure Agent 2 has run and populated state.metadata['mapped_rows']."
            )
            state.status = JobStatus.AWAITING_REVIEW
            return state

        try:
            report = analyze_quality(mapped_rows, llm_adapter=self.llm_adapter)
        except Exception as e:
            logger.error(f"DataQualityAgent: analyze_quality failed: {e}")
            state.errors.append(f"Quality analysis error: {e}")
            state.status = JobStatus.AWAITING_REVIEW
            return state

        state.quality_issues = report.issues
        state.recommendations = report.recommendations
        state.metadata["quality_report"] = {
            "total_rows_scanned": report.total_rows_scanned,
            "total_issues": report.total_issues,
            "summary": report.summary,
        }
        state.status = JobStatus.AWAITING_REVIEW
        return state
