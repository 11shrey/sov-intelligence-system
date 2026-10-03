"""Agent 2: Schema Mapping Agent

Responsible for:
- Reading raw column headers from the selected sheet via the shared SOVProcessingState.
- Mapping each raw header to one of the 17 standard SOV target fields.
- Computing matching confidence scores and specifying the method
  (exact, normalized, semantic_alias, fuzzy, heuristic, llm, unmapped).
- Routing low-confidence/ambiguous columns to an optional LLM semantic fallback.
- Producing SchemaMapping objects and populating state.schema_mappings.
- Respecting the human-in-the-loop boundary: Agent 2 NEVER writes final data.

Architecture:
    Deterministic cascade (stages 1-4) → LLM fallback (stage 5) → unmapped fallback.

    Stage 1  Exact match against 17 canonical names  (confidence 1.00)
    Stage 2  Normalised (lower-case, whitespace/punct) match  (confidence 0.98)
    Stage 3  Curated domain alias dictionary  (confidence 0.95)
    Stage 4  RapidFuzz token-sort fuzzy match with semantic safety guards  (0.50–0.90)
    Stage 5  Optional LLM semantic fallback with post-validation  (configurable)

Integration with shared state:
    Input  : state.metadata.get("raw_columns") — list of source column names
              state.sheet_analysis             — Agent 1 analysis results
              state.selected_sheet             — selected sheet name
              state.metadata.get("agent1_suggestions") — optional upstream hints
    Output : state.schema_mappings            — list[SchemaMapping]
             state.metadata["unmapped_source_columns"]
             state.metadata["missing_target_fields"]
             state.metadata["mapping_report"]  — summary dict

Public API (also usable standalone without the state pipeline):
    map_columns(source_columns, agent1_suggestions, llm_adapter) -> list[SchemaMapping]
    map_schema(sheet_data, llm_adapter)                          -> SchemaMappingResult
    map_single_column(source_col, agent1_suggestion, llm_adapter) -> SchemaMapping
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from rapidfuzz import fuzz, process as fuzz_process

from app.orchestration.state import SOVProcessingState, JobStatus
from app.models.schema_models import (
    SchemaMapping,
    SchemaMappingReport,
    TARGET_SOV_FIELDS,
    TargetSOVField,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Authoritative 17 Canonical SOV Fields (in exact required order)
# ---------------------------------------------------------------------------

CANONICAL_SOV_FIELDS: list[str] = TARGET_SOV_FIELDS  # reuse shared source of truth


# ---------------------------------------------------------------------------
# Schema field definitions (for LLM prompt enrichment)
# ---------------------------------------------------------------------------

_SOV_FIELD_DEFINITIONS: list[dict] = [
    {"field": "Reference", "description": "Unique identifier for the property (Loc #, ID, Site ID)."},
    {"field": "Address", "description": "Full street address of the insured property."},
    {"field": "City", "description": "City where the insured property is located."},
    {"field": "State", "description": "State or region (2-letter abbreviation preferred)."},
    {"field": "Zip", "description": "Postal / ZIP code for geographic risk identification."},
    {"field": "County", "description": "County for regional risk analysis."},
    {"field": "Country", "description": "Country; defines jurisdiction for policy coverage."},
    {"field": "Building Value", "description": "Insured value of the building structure (replacement cost / RCV)."},
    {"field": "Contents", "description": "Value of personal property or contents (BPP)."},
    {"field": "BI", "description": "Business Income / Business Interruption coverage value."},
    {"field": "Occupancy", "description": "Use or purpose of the building (residential, commercial, industrial)."},
    {"field": "Construction", "description": "Construction type or material (wood, steel, masonry)."},
    {"field": "Storeys", "description": "Number of floors / stories in the building."},
    {"field": "Number of Buildings", "description": "Total number of buildings at the location."},
    {"field": "Year Built", "description": "Year the building was constructed."},
    {"field": "Fire Sprinklers (Y/N)", "description": "Whether fire sprinkler systems are installed (Y/N/Yes/No)."},
    {"field": "Other", "description": "Additional insured values not classified elsewhere."},
]


# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------

_CONFIDENCE_APPROVED = 0.85   # >= this → approved
_CONFIDENCE_REVIEW = 0.50     # >= this (but < approved) → needs_review
                               # < CONFIDENCE_REVIEW → rejected


# ---------------------------------------------------------------------------
# Mapping status constants
# ---------------------------------------------------------------------------

_STATUS_APPROVED = "approved"
_STATUS_NEEDS_REVIEW = "needs_review"
_STATUS_REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Normalization Helper
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lower-case, collapse whitespace/punctuation to single spaces, strip."""
    if not text:
        return ""
    t = text.replace("_", " ").replace("-", " ")
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


# ---------------------------------------------------------------------------
# Curated Domain Alias Dictionary
# ---------------------------------------------------------------------------

_ALIAS_TABLE: dict[str, str] = {
    # Reference
    "property id": "Reference",
    "property_id": "Reference",
    "property reference": "Reference",
    "property_reference": "Reference",
    "policy reference": "Reference",
    "policy_reference": "Reference",
    "loc": "Reference",
    "loc #": "Reference",
    "loc#": "Reference",
    "loc no": "Reference",
    "loc num": "Reference",
    "location #": "Reference",
    "location no": "Reference",
    "location num": "Reference",
    "location number": "Reference",
    "location id": "Reference",
    "site id": "Reference",
    "site #": "Reference",
    "site no": "Reference",
    "ref": "Reference",
    "ref #": "Reference",
    "ref no": "Reference",
    "id": "Reference",
    "record id": "Reference",

    # Address
    "street address": "Address",
    "street_address": "Address",
    "property address": "Address",
    "property_address": "Address",
    "full address": "Address",
    "full_address": "Address",
    "addr": "Address",
    "address 1": "Address",
    "address1": "Address",
    "street": "Address",
    "street location": "Address",
    "street_location": "Address",
    "location address": "Address",
    "site address": "Address",

    # City
    "city name": "City",
    "city_name": "City",
    "town": "City",
    "municipality": "City",

    # State
    "state name": "State",
    "state_name": "State",
    "state code": "State",
    "state_code": "State",
    "st": "State",
    "province": "State",
    "region": "State",

    # Zip
    "postal code": "Zip",
    "postal_code": "Zip",
    "zip code": "Zip",
    "zip_code": "Zip",
    "zipcode": "Zip",
    "post code": "Zip",
    "postcode": "Zip",

    # County
    "county name": "County",
    "county_name": "County",
    "parish": "County",
    "borough": "County",

    # Country
    "country name": "Country",
    "country_name": "Country",
    "nation": "Country",
    "country code": "Country",

    # Building Value
    "building value": "Building Value",
    "building_value": "Building Value",
    "building cost": "Building Value",
    "building_cost": "Building Value",
    "building insured value": "Building Value",
    "building_insured_value": "Building Value",
    "replacement cost": "Building Value",
    "replacement_cost": "Building Value",
    "bldg repl cost": "Building Value",
    "bldg value": "Building Value",
    "building rcv": "Building Value",
    "building tiv": "Building Value",
    "building rc": "Building Value",
    "bldg rcv": "Building Value",
    "bldg limit": "Building Value",
    "structure value": "Building Value",

    # Contents
    "contents value": "Contents",
    "contents_value": "Contents",
    "content value": "Contents",
    "content_value": "Contents",
    "personal property value": "Contents",
    "personal_property_value": "Contents",
    "personal property": "Contents",
    "bpp": "Contents",
    "contents tiv": "Contents",
    "pp value": "Contents",
    "stock value": "Contents",
    "equipment value": "Contents",
    "inventory": "Contents",

    # BI
    "business income": "BI",
    "business_income": "BI",
    "business income value": "BI",
    "business_income_value": "BI",
    "business interruption": "BI",
    "business_interruption": "BI",
    "bi limit": "BI",
    "bi value": "BI",
    "loss of income": "BI",
    "time element": "BI",
    "business interruption value": "BI",

    # Occupancy
    "occupancy type": "Occupancy",
    "occupancy_type": "Occupancy",
    "building use": "Occupancy",
    "building_use": "Occupancy",
    "property use": "Occupancy",
    "property_use": "Occupancy",
    "use": "Occupancy",
    "use type": "Occupancy",
    "occupancy": "Occupancy",
    "primary use": "Occupancy",

    # Construction
    "construction type": "Construction",
    "construction_type": "Construction",
    "construction material": "Construction",
    "construction_material": "Construction",
    "construction class": "Construction",
    "const type": "Construction",
    "const class": "Construction",
    "iso construction": "Construction",
    "structure type": "Construction",
    "material": "Construction",
    "materials": "Construction",
    "building material": "Construction",
    "building_material": "Construction",

    # Storeys
    "number of storeys": "Storeys",
    "number_of_storeys": "Storeys",
    "number of stories": "Storeys",
    "number_of_stories": "Storeys",
    "stories": "Storeys",
    "storeys": "Storeys",
    "floors": "Storeys",
    "floor count": "Storeys",
    "floor_count": "Storeys",
    "floors count": "Storeys",
    "num stories": "Storeys",
    "no stories": "Storeys",
    "no. stories": "Storeys",
    "no of stories": "Storeys",
    "no. of stories": "Storeys",
    "number of floors": "Storeys",
    "# stories": "Storeys",

    # Number of Buildings
    "building count": "Number of Buildings",
    "building_count": "Number of Buildings",
    "building qty": "Number of Buildings",
    "building_qty": "Number of Buildings",
    "building quantity": "Number of Buildings",
    "bldg qty": "Number of Buildings",
    "bldg quantity": "Number of Buildings",
    "number of buildings": "Number of Buildings",
    "number_of_buildings": "Number of Buildings",
    "num buildings": "Number of Buildings",
    "bldg count": "Number of Buildings",
    "count of buildings": "Number of Buildings",
    "number buildings": "Number of Buildings",

    # Year Built
    "construction year": "Year Built",
    "construction_year": "Year Built",
    "year constructed": "Year Built",
    "year_constructed": "Year Built",
    "yr built": "Year Built",
    "year build": "Year Built",
    "yr. built": "Year Built",
    "yr blt": "Year Built",
    "year blt": "Year Built",

    # Fire Sprinklers (Y/N)
    "sprinklers": "Fire Sprinklers (Y/N)",
    "fire sprinklers": "Fire Sprinklers (Y/N)",
    "fire_sprinklers": "Fire Sprinklers (Y/N)",
    "sprinkler system": "Fire Sprinklers (Y/N)",
    "sprinkler_system": "Fire Sprinklers (Y/N)",
    "fire prot": "Fire Sprinklers (Y/N)",
    "fire prot.": "Fire Sprinklers (Y/N)",
    "fire protection": "Fire Sprinklers (Y/N)",
    "sprinkler": "Fire Sprinklers (Y/N)",
    "sprinklered": "Fire Sprinklers (Y/N)",

    # Other
    "other value": "Other",
    "other_value": "Other",
    "additional value": "Other",
    "additional_value": "Other",
    "other insured value": "Other",
    "other_insured_value": "Other",
    "misc value": "Other",
    "miscellaneous value": "Other",
}

# Pre-normalized lookup table: normalised key → canonical target name
_NORMALIZED_ALIAS_TABLE: dict[str, str] = {
    _normalise(k): v for k, v in _ALIAS_TABLE.items()
}


# ---------------------------------------------------------------------------
# Semantic Safety Guards
# ---------------------------------------------------------------------------

def _is_semantically_safe(norm_source: str, target_field: str) -> bool:
    """
    Ensures a fuzzy, heuristic, or LLM candidate mapping is semantically valid.
    Prevents false positives on TIV, generic tokens, metadata, and geographic scopes.
    """
    source_tokens = set(norm_source.split())

    # 1. Total Insured Value (TIV) Isolation
    tiv_tokens = {"tiv", "total insured value", "total value", "total insurable value", "total tiv"}
    if (
        norm_source in tiv_tokens
        or ("tiv" in source_tokens)
        or ({"total", "insured", "value"}.issubset(source_tokens))
    ):
        if target_field != "Other":
            return False

    # 2. Reject purely irrelevant metadata tokens
    irrelevant_tokens = {
        "comment", "comments", "notes", "status", "policy", "broker",
        "account", "contact", "internal", "record", "system", "item",
        "asset", "cost center", "irrelevant", "unnamed", "misc"
    }
    if source_tokens.intersection(irrelevant_tokens) and norm_source not in _NORMALIZED_ALIAS_TABLE:
        return False

    # 3. Ambiguous columns (e.g., value_2, col_1)
    if re.match(r"^(val|value|col|column|data)[_\s]*\d+$", norm_source):
        return False

    # 4. Strict Geographic Scope Protection
    geo_anchors = {
        "city": "City",
        "state": "State",
        "province": "State",
        "zip": "Zip",
        "postal": "Zip",
        "county": "County",
        "country": "Country",
        "nation": "Country",
    }
    for token, geo_target in geo_anchors.items():
        if token in source_tokens:
            if target_field != geo_target:
                return False

    # 5. Quantity vs Financial Value distinction
    if "count" in source_tokens or "quantity" in source_tokens or "qty" in source_tokens:
        if target_field not in ("Number of Buildings", "Storeys"):
            return False

    # 6. Street / Address vs Reference protection
    if any(t in source_tokens for t in ("street", "avenue", "road", "drive", "lane", "blvd")):
        if target_field == "Reference" and not any(
            t in source_tokens for t in ("id", "ref", "num", "no", "number")
        ):
            return False

    # 7. Financial/Cost/Value vs Construction material protection
    if target_field == "Construction":
        if source_tokens.intersection({"cost", "value", "val", "price", "limit", "usd", "expense", "rcv"}):
            return False

    # 8. Target-specific semantic evidence requirement
    def _matches_any(synonyms: list[str], threshold: float = 75.0) -> bool:
        for st in source_tokens:
            for syn in synonyms:
                if fuzz.ratio(st, syn) >= threshold:
                    return True
        return False

    if target_field == "Reference":
        return _matches_any(["ref", "reference", "loc", "location", "property", "site", "id"])
    elif target_field == "Address":
        return _matches_any(["address", "addr", "street", "strt", "location"])
    elif target_field == "City":
        return _matches_any(["city", "town", "municipality"])
    elif target_field == "State":
        return _matches_any(["state", "st", "province", "region"])
    elif target_field == "Zip":
        return _matches_any(["zip", "postal", "postcode", "zipcode"])
    elif target_field == "County":
        return _matches_any(["county", "parish", "borough"])
    elif target_field == "Country":
        return _matches_any(["country", "nation"])
    elif target_field == "Building Value":
        has_bldg = _matches_any(["building", "bldg", "structure"])
        has_val = _matches_any(["value", "val", "cost", "cst", "repl", "rcv", "limit"])
        return (has_bldg and has_val) or _matches_any(["replacement_cost"])
    elif target_field == "Contents":
        return _matches_any(["content", "contents", "bpp", "personal", "prop", "stock", "equipment"])
    elif target_field == "BI":
        return _matches_any(["bi", "business", "interruption", "income", "loss"])
    elif target_field == "Occupancy":
        return _matches_any(["occupancy", "occ", "use", "purpose"])
    elif target_field == "Construction":
        return _matches_any(["construction", "const", "material", "class", "structure", "framing", "masonry", "frame"])
    elif target_field == "Storeys":
        return _matches_any(["storey", "storeys", "story", "stories", "floor", "floors", "level"])
    elif target_field == "Number of Buildings":
        return _matches_any(["building", "bldg"]) and _matches_any(["count", "num", "number", "quantity", "qty"])
    elif target_field == "Year Built":
        return _matches_any(["year", "yr"]) and _matches_any(["built", "blt", "const", "constructed"])
    elif target_field == "Fire Sprinklers (Y/N)":
        return _matches_any(["fire", "sprinkler", "sprinklers", "prot"])
    elif target_field == "Other":
        return _matches_any(["other", "additional", "misc", "miscellaneous"])

    return False


# ---------------------------------------------------------------------------
# LLM Adapter
# ---------------------------------------------------------------------------

_QWEN_SYSTEM_PROMPT = """You are a schema-mapping assistant for an insurance Statement of Values (SOV) dataset.
Your task is to identify which canonical SOV field, if any, best corresponds to the given source column name.

CRITICAL RULES:
1. Do not invent any field names.
2. Only select a target field from the 17 authoritative canonical SOV fields provided.
3. If the source column is ambiguous, metadata/irrelevant, or does not clearly correspond to any canonical field, set "target_field" to null and "status" to "rejected".
4. Total Insured Value / TIV must NOT be mapped to Building Value or Contents.
5. Geographic fields (City, State, Zip, County, Country) must not be confused with financial or property fields.
6. Quantity/count fields must not be confused with monetary value fields.
7. Construction/material fields must not be confused with building monetary value.
8. Do not perform any data transformations on underlying cell values.
9. You must respond in valid JSON format ONLY with keys: "target_field", "confidence", "reasoning", "status".
"""


def _build_llm_user_prompt(payload: dict[str, Any]) -> str:
    source_column = payload.get("source_column", "")
    canonical_fields = payload.get("canonical_fields", CANONICAL_SOV_FIELDS)
    field_definitions = payload.get("field_definitions", _SOV_FIELD_DEFINITIONS)
    candidate_targets = payload.get("candidate_targets", [])
    deterministic_evidence = payload.get("deterministic_evidence", {})
    agent1_suggestion = payload.get("agent1_suggestion", None)

    lines = [
        f'SOURCE COLUMN TO MAP: "{source_column}"\n',
        "CANONICAL SOV FIELDS (choose exactly one, or null):",
        json.dumps(canonical_fields, indent=2),
        "\nFIELD DEFINITIONS:",
        json.dumps(field_definitions, indent=2),
    ]

    if candidate_targets:
        lines.append(f"\nCANDIDATE TARGETS (from heuristic matching): {json.dumps(candidate_targets)}")
    if deterministic_evidence:
        lines.append(f"DETERMINISTIC EVIDENCE: {json.dumps(deterministic_evidence)}")
    if agent1_suggestion:
        lines.append(f"UPSTREAM AGENT 1 SUGGESTION (Advisory Only): {json.dumps(agent1_suggestion)}")

    lines.append("""
OUTPUT FORMAT INSTRUCTIONS:
Return a JSON object only:
{
  "target_field": "<Exact canonical field name or null>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<Human-readable explanation>",
  "status": "<approved | needs_review | rejected>"
}
""")
    return "\n".join(lines)


def _parse_llm_json_response(content: str) -> Optional[dict[str, Any]]:
    """Parses and validates a raw JSON text response from an LLM."""
    if not content:
        return None
    try:
        text = content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            return None

        target = parsed.get("target_field")
        if target is not None and str(target).strip() == "":
            target = None

        try:
            conf = float(parsed.get("confidence", 0.70))
            conf = max(0.0, min(1.0, conf))
        except (ValueError, TypeError):
            conf = 0.70

        reasoning = str(parsed.get("reasoning", "Semantic LLM mapping interpretation."))
        status = str(parsed.get("status", "needs_review")).lower()

        return {
            "target_field": target if (target in CANONICAL_SOV_FIELDS or target is None) else None,
            "confidence": conf if target in CANONICAL_SOV_FIELDS else 0.0,
            "reasoning": reasoning,
            "status": status,
        }
    except Exception as e:
        logger.warning(f"Failed to parse LLM JSON response: {e}")
        return None


def _call_qwen_api(
    payload: dict[str, Any],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
    http_client: Optional[Any] = None,
) -> Optional[dict[str, Any]]:
    """Calls the Qwen model via DashScope's OpenAI-compatible API. Fails safely."""
    api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.debug("DASHSCOPE_API_KEY not configured; skipping Qwen API call.")
        return None

    model = model_name or os.getenv("SOV_LLM_MODEL", "qwen3.7-plus")
    base_url = (
        base_url or os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    ).rstrip("/")
    timeout_sec = float(timeout or os.getenv("SOV_LLM_TIMEOUT", "15.0"))

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_prompt = _build_llm_user_prompt(payload)
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": _QWEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }

    try:
        if http_client is not None:
            resp = http_client.post(endpoint, headers=headers, json=request_body, timeout=timeout_sec)
        else:
            import httpx
            with httpx.Client(timeout=timeout_sec) as client:
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
        return _parse_llm_json_response(content)

    except Exception as e:
        logger.warning(f"Qwen API call error: {e}")
        return None


class LLMAdapter:
    """
    Configurable, mockable adapter for semantic LLM mapping fallback.
    Supports injected callables (for tests/mocks) and real Qwen cloud integration.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        llm_callable: Optional[Callable[[dict], Optional[dict]]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        http_client: Optional[Any] = None,
    ):
        self.model_name = model_name or os.getenv("SOV_LLM_MODEL", "qwen3.7-plus")
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or os.getenv(
            "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        self.timeout = float(timeout or os.getenv("SOV_LLM_TIMEOUT", "15.0"))
        self.http_client = http_client

        if llm_callable is not None:
            self.llm_callable = llm_callable
        elif self.api_key and self.model_name != "mock-adapter":
            self.llm_callable = lambda payload: _call_qwen_api(
                payload=payload,
                api_key=self.api_key,
                model_name=self.model_name,
                base_url=self.base_url,
                timeout=self.timeout,
                http_client=self.http_client,
            )
        else:
            self.llm_callable = None

    def map_column_semantically(
        self,
        source_column: str,
        candidate_targets: list[str],
        deterministic_evidence: dict[str, Any],
        agent1_suggestion: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Queries the LLM for an ambiguous column mapping. Returns structured dict or None."""
        if self.llm_callable is not None:
            prompt_payload = {
                "source_column": source_column,
                "canonical_fields": CANONICAL_SOV_FIELDS,
                "field_definitions": _SOV_FIELD_DEFINITIONS,
                "candidate_targets": candidate_targets,
                "deterministic_evidence": deterministic_evidence,
                "agent1_suggestion": agent1_suggestion,
            }
            try:
                response = self.llm_callable(prompt_payload)
                if isinstance(response, dict) and "target_field" in response:
                    target = response.get("target_field")
                    norm_source = _normalise(source_column)
                    if target is not None:
                        if target not in CANONICAL_SOV_FIELDS or not _is_semantically_safe(norm_source, target):
                            logger.warning(
                                f"LLM suggested target '{target}' for '{source_column}' "
                                "failed semantic validation."
                            )
                            return {
                                "target_field": None,
                                "confidence": 0.0,
                                "reasoning": (
                                    f"LLM suggestion '{target}' failed semantic safety validation "
                                    f"for source column '{source_column}'."
                                ),
                                "status": "rejected",
                            }
                    return response
            except Exception as e:
                logger.warning(f"LLM adapter call failed for column '{source_column}': {e}")
                return None

        return None


# ---------------------------------------------------------------------------
# Internal data class for mapping results (not exported as a public model)
# ---------------------------------------------------------------------------

class _MappingResult:
    """Internal result container (not a Pydantic model — avoids model duplication)."""

    def __init__(
        self,
        mappings: list[SchemaMapping],
        mapped_rows: list[dict[str, Any]],
        unmapped_source: list[str],
        unmapped_target: list[str],
        metadata: dict[str, Any],
    ):
        self.mappings = mappings
        self.mapped_rows = mapped_rows
        self.unmapped_source = unmapped_source
        self.unmapped_target = unmapped_target
        self.metadata = metadata


# ---------------------------------------------------------------------------
# Stage-by-Stage Matching Engine
# ---------------------------------------------------------------------------

def _map_single_column_internal(
    source_col: str,
    agent1_suggestion: Optional[dict[str, Any]] = None,
    llm_adapter: Optional[LLMAdapter] = None,
) -> SchemaMapping:
    """
    Deterministic cascade + Semantic LLM router for a single source column.
    Returns a SchemaMapping (shared contract).
    """
    norm_source = _normalise(source_col)

    if not norm_source:
        return SchemaMapping(
            source_column=source_col,
            target_field=None,
            confidence=0.0,
            method="unmapped",
            reasoning=f"Empty or unparseable source column '{source_col}'.",
            status=_STATUS_REJECTED,
        )

    # ── Stage 1: Exact match ───────────────────────────────────────────────
    for target in CANONICAL_SOV_FIELDS:
        if source_col == target:
            return SchemaMapping(
                source_column=source_col,
                target_field=target,
                confidence=1.0,
                method="exact",
                reasoning=f"Exact match for canonical field '{target}'.",
                status=_STATUS_APPROVED,
            )

    # ── Stage 2: Normalised match ──────────────────────────────────────────
    for target in CANONICAL_SOV_FIELDS:
        if norm_source == _normalise(target):
            return SchemaMapping(
                source_column=source_col,
                target_field=target,
                confidence=0.98,
                method="normalized",
                reasoning=f"Normalised match '{source_col}' -> '{target}'.",
                status=_STATUS_APPROVED,
            )

    # ── Stage 3: Curated Domain Alias lookup ──────────────────────────────
    if norm_source in _NORMALIZED_ALIAS_TABLE:
        target = _NORMALIZED_ALIAS_TABLE[norm_source]
        if target in CANONICAL_SOV_FIELDS:
            return SchemaMapping(
                source_column=source_col,
                target_field=target,
                confidence=0.95,
                method="semantic_alias",
                reasoning=f"Source column '{source_col}' matched curated alias -> '{target}'.",
                status=_STATUS_APPROVED,
            )

    # ── Stage 4: RapidFuzz candidate generation with semantic safety ───────
    fuzzy_candidates = list(CANONICAL_SOV_FIELDS) + list(_ALIAS_TABLE.keys())
    all_norm_candidates = [_normalise(c) for c in fuzzy_candidates]

    best_result = fuzz_process.extractOne(
        norm_source,
        all_norm_candidates,
        scorer=fuzz.token_sort_ratio,
    )

    fuzzy_target: Optional[str] = None
    fuzzy_confidence: float = 0.0
    fuzzy_score: float = 0.0

    if best_result is not None:
        best_match, fuzzy_score, best_idx = best_result
        best_candidate = fuzzy_candidates[best_idx]

        if best_candidate in CANONICAL_SOV_FIELDS:
            fuzzy_target = best_candidate
        else:
            fuzzy_target = _ALIAS_TABLE.get(best_candidate)

        if fuzzy_target and fuzzy_target in CANONICAL_SOV_FIELDS:
            if _is_semantically_safe(norm_source, fuzzy_target):
                fuzzy_confidence = round(fuzzy_score / 100.0 * 0.90, 4)
            else:
                fuzzy_target = None
                fuzzy_confidence = 0.0

    if fuzzy_confidence >= _CONFIDENCE_APPROVED and fuzzy_target:
        return SchemaMapping(
            source_column=source_col,
            target_field=fuzzy_target,
            confidence=fuzzy_confidence,
            method="fuzzy",
            reasoning=(
                f"Fuzzy token-sort match ({fuzzy_score:.1f}/100) between "
                f"'{norm_source}' and '{fuzzy_target}'."
            ),
            status=_STATUS_APPROVED,
        )

    # ── Stage 5: LLM Fallback ─────────────────────────────────────────────
    upstream_target: Optional[str] = None
    if agent1_suggestion and isinstance(agent1_suggestion, dict):
        suggested = agent1_suggestion.get("target_field")
        if suggested in CANONICAL_SOV_FIELDS and _is_semantically_safe(norm_source, suggested):
            upstream_target = suggested

    if llm_adapter is not None:
        deterministic_evidence = {
            "fuzzy_candidate": fuzzy_target,
            "fuzzy_confidence": fuzzy_confidence,
            "upstream_suggestion": upstream_target,
        }
        candidates = [fuzzy_target] if fuzzy_target else CANONICAL_SOV_FIELDS[:5]
        llm_res = llm_adapter.map_column_semantically(
            source_column=source_col,
            candidate_targets=candidates,
            deterministic_evidence=deterministic_evidence,
            agent1_suggestion=agent1_suggestion,
        )
        if llm_res and isinstance(llm_res, dict):
            target = llm_res.get("target_field")
            conf = float(llm_res.get("confidence", 0.70))
            reason = llm_res.get("reasoning", "Semantic LLM mapping.")
            status_str = llm_res.get("status", "needs_review")

            if target is not None:
                if target not in CANONICAL_SOV_FIELDS or not _is_semantically_safe(norm_source, target):
                    logger.warning(
                        f"LLM suggested '{target}' for '{source_col}', "
                        "but failed semantic safety validation. Rejected."
                    )
                    return SchemaMapping(
                        source_column=source_col,
                        target_field=None,
                        confidence=0.0,
                        method="llm",
                        reasoning=(
                            f"LLM suggested '{target}', which failed semantic safety validation. "
                            "Marked as rejected."
                        ),
                        status=_STATUS_REJECTED,
                    )

            if target is None or status_str == "rejected":
                final_status = _STATUS_REJECTED
            else:
                # LLM results always require human review regardless of stated status
                final_status = _STATUS_NEEDS_REVIEW

            return SchemaMapping(
                source_column=source_col,
                target_field=target if target in CANONICAL_SOV_FIELDS else None,
                confidence=conf if target else 0.0,
                method="llm",
                reasoning=reason,
                status=final_status if target else _STATUS_REJECTED,
            )

    # Review-confidence fuzzy fallback
    if fuzzy_confidence >= _CONFIDENCE_REVIEW and fuzzy_target:
        return SchemaMapping(
            source_column=source_col,
            target_field=fuzzy_target,
            confidence=fuzzy_confidence,
            method="fuzzy",
            reasoning=(
                f"Moderate confidence match ({fuzzy_score:.1f}/100) -> '{fuzzy_target}'. "
                "Requires human review."
            ),
            status=_STATUS_NEEDS_REVIEW,
        )

    # Upstream suggestion fallback
    if upstream_target:
        return SchemaMapping(
            source_column=source_col,
            target_field=upstream_target,
            confidence=0.75,
            method="heuristic",
            reasoning=(
                f"Validated upstream suggestion -> '{upstream_target}'. "
                "Marked for review."
            ),
            status=_STATUS_NEEDS_REVIEW,
        )

    # ── Stage 6: Unmapped / Rejected ──────────────────────────────────────
    is_ambiguous = bool(re.search(r"\d", norm_source)) or len(norm_source.split()) > 3
    final_status = _STATUS_NEEDS_REVIEW if is_ambiguous else _STATUS_REJECTED
    confidence = 0.35 if is_ambiguous else 0.0

    return SchemaMapping(
        source_column=source_col,
        target_field=None,
        confidence=confidence,
        method="unmapped",
        reasoning=(
            f"Could not confidently map '{source_col}' to any of the 17 canonical SOV fields. "
            f"Marked as {final_status}."
        ),
        status=final_status,
    )


# ---------------------------------------------------------------------------
# Conflict Validation
# ---------------------------------------------------------------------------

def _validate_and_resolve_conflicts(mappings: list[SchemaMapping]) -> list[SchemaMapping]:
    """Detects duplicate target collisions and applies confidence penalties."""
    target_to_cols: dict[str, list[int]] = {}
    for idx, m in enumerate(mappings):
        if m.target_field and m.status != _STATUS_REJECTED:
            target_to_cols.setdefault(m.target_field, []).append(idx)

    validated = list(mappings)

    for target_field, indices in target_to_cols.items():
        if len(indices) > 1:
            competing_cols = [mappings[i].source_column for i in indices]
            for i in indices:
                orig = mappings[i]
                new_conf = round(orig.confidence * 0.60, 4)
                validated[i] = SchemaMapping(
                    source_column=orig.source_column,
                    target_field=orig.target_field,
                    confidence=new_conf,
                    method=orig.method,
                    reasoning=(
                        f"{orig.reasoning} [CONFLICT: Multiple columns {competing_cols} "
                        f"mapped to target '{target_field}'; marked for review.]"
                    ),
                    status=_STATUS_NEEDS_REVIEW,
                )

    return validated


# ---------------------------------------------------------------------------
# Canonical 17-field row builder
# ---------------------------------------------------------------------------

def _build_canonical_mapped_rows(
    source_rows: list[dict[str, Any]],
    mappings: list[SchemaMapping],
) -> list[dict[str, Any]]:
    """
    Builds canonical mapped rows with exactly the 17 canonical fields in exact order.
    NEVER modifies raw values. Missing targets are set to None (not fabricated).
    """
    source_to_target: dict[str, str] = {
        m.source_column: m.target_field
        for m in mappings
        if m.target_field and m.status != _STATUS_REJECTED
    }

    mapped_rows: list[dict[str, Any]] = []
    for row in source_rows:
        canonical_row: dict[str, Any] = {field: None for field in CANONICAL_SOV_FIELDS}

        for src_col, val in row.items():
            target_field = source_to_target.get(src_col)
            if target_field and target_field in canonical_row:
                if canonical_row[target_field] is None:
                    canonical_row[target_field] = val

        mapped_rows.append(canonical_row)

    return mapped_rows


# ---------------------------------------------------------------------------
# Public standalone API
# ---------------------------------------------------------------------------

def map_single_column(
    source_col: str,
    agent1_suggestion: Optional[dict[str, Any]] = None,
    llm_adapter: Optional[LLMAdapter] = None,
) -> SchemaMapping:
    """Map a single source column header to a canonical SOV field."""
    return _map_single_column_internal(
        source_col=source_col,
        agent1_suggestion=agent1_suggestion,
        llm_adapter=llm_adapter,
    )


def map_columns(
    source_columns: list[str],
    agent1_suggestions: Optional[dict[str, dict[str, Any]]] = None,
    llm_adapter: Optional[LLMAdapter] = None,
) -> list[SchemaMapping]:
    """
    Map a list of source column headers to canonical SOV fields.
    Returns validated, conflict-resolved SchemaMapping list.
    """
    raw_mappings = [
        _map_single_column_internal(
            source_col=col,
            agent1_suggestion=(agent1_suggestions or {}).get(col),
            llm_adapter=llm_adapter,
        )
        for col in source_columns
    ]
    return _validate_and_resolve_conflicts(raw_mappings)


def map_schema(
    sheet_data: list[dict[str, Any]],
    schema: Optional[list[dict]] = None,
    llm_adapter: Optional[LLMAdapter] = None,
) -> _MappingResult:
    """
    Row-dictionary based entrypoint. Accepts list of row dicts (header → value).
    Returns a _MappingResult with canonical 17-field mapped_rows.
    """
    if not sheet_data:
        return _MappingResult(
            mappings=[],
            mapped_rows=[],
            unmapped_source=[],
            unmapped_target=list(CANONICAL_SOV_FIELDS),
            metadata={"mapping_mode": "direct_rows", "empty": True},
        )

    source_columns: list[str] = []
    seen: set[str] = set()
    for row in sheet_data:
        for col in row.keys():
            if col not in seen:
                source_columns.append(col)
                seen.add(col)

    raw_mappings = [
        _map_single_column_internal(source_col=col, llm_adapter=llm_adapter)
        for col in source_columns
    ]
    validated_mappings = _validate_and_resolve_conflicts(raw_mappings)
    mapped_rows = _build_canonical_mapped_rows(sheet_data, validated_mappings)

    unmapped_source = [
        m.source_column for m in validated_mappings
        if m.status == _STATUS_REJECTED or m.target_field is None
    ]
    mapped_target_fields = {
        m.target_field for m in validated_mappings
        if m.target_field and m.status != _STATUS_REJECTED
    }
    unmapped_target = [f for f in CANONICAL_SOV_FIELDS if f not in mapped_target_fields]

    return _MappingResult(
        mappings=validated_mappings,
        mapped_rows=mapped_rows,
        unmapped_source=unmapped_source,
        unmapped_target=unmapped_target,
        metadata={
            "mapping_mode": "direct_rows",
            "sample_only": False,
            "total_source_columns": len(source_columns),
            "total_mapped_targets": len(mapped_target_fields),
            "llm_used": llm_adapter is not None,
        },
    )


def map_agent1_output(
    agent1_output: Union[dict[str, Any], str, Path],
    llm_adapter: Optional[LLMAdapter] = None,
) -> _MappingResult:
    """
    Main Agent 2 entrypoint for external Agent 1 JSON contract integration.
    Parses Agent 1 JSON, extracts source columns, runs the mapping cascade.
    """
    # 1. Parse JSON input
    if isinstance(agent1_output, (str, Path)):
        if isinstance(agent1_output, Path) or (
            isinstance(agent1_output, str)
            and (agent1_output.endswith(".json") or os.path.exists(agent1_output))
        ):
            with open(agent1_output, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(agent1_output)
    else:
        data = agent1_output  # preserve immutability — do NOT modify

    if not isinstance(data, dict):
        raise ValueError("Agent 1 output must be a valid dictionary or JSON object.")

    # 2. Extract sheet analysis and sample rows
    sheet_analysis = data.get("sheet_analysis", {})
    selected_sheet = sheet_analysis.get("selected_sheet", "")
    sheets = sheet_analysis.get("sheets", [])

    sheet_obj: Optional[dict[str, Any]] = None
    if sheets:
        for s in sheets:
            if s.get("sheet_name") == selected_sheet:
                sheet_obj = s
                break
        if sheet_obj is None and sheets:
            sheet_obj = sheets[0]

    raw_sample_rows = sheet_obj.get("sample_rows", []) if sheet_obj else []
    source_columns: list[str] = []
    parsed_rows: list[dict[str, Any]] = []

    if raw_sample_rows and isinstance(raw_sample_rows, list):
        header_row = raw_sample_rows[0]
        if isinstance(header_row, list):
            source_columns = [
                str(c) if c is not None else f"Col_{i}"
                for i, c in enumerate(header_row)
            ]
            for data_row in raw_sample_rows[1:]:
                if isinstance(data_row, list):
                    row_dict = {
                        source_columns[i]: data_row[i]
                        for i in range(min(len(source_columns), len(data_row)))
                    }
                    parsed_rows.append(row_dict)

    if not source_columns and "raw_rows" in data:
        parsed_rows = data.get("raw_rows", [])
        seen_cols: set[str] = set()
        for r in parsed_rows:
            for k in r.keys():
                if k not in seen_cols:
                    source_columns.append(k)
                    seen_cols.add(k)

    # 3. Extract upstream suggestions
    upstream_suggestions: dict[str, dict[str, Any]] = {}
    for m in data.get("mappings", []):
        if isinstance(m, dict) and "source_column" in m:
            upstream_suggestions[m["source_column"]] = m

    # 4. Map each source column
    raw_mappings = [
        _map_single_column_internal(
            source_col=col,
            agent1_suggestion=upstream_suggestions.get(col),
            llm_adapter=llm_adapter,
        )
        for col in source_columns
    ]

    # 5. Validate & resolve conflicts
    validated_mappings = _validate_and_resolve_conflicts(raw_mappings)

    # 6. Build canonical rows
    mapped_rows = _build_canonical_mapped_rows(parsed_rows, validated_mappings)

    unmapped_source = [
        m.source_column for m in validated_mappings
        if m.status == _STATUS_REJECTED or m.target_field is None
    ]
    mapped_target_fields = {
        m.target_field for m in validated_mappings
        if m.target_field and m.status != _STATUS_REJECTED
    }
    unmapped_target = [f for f in CANONICAL_SOV_FIELDS if f not in mapped_target_fields]

    return _MappingResult(
        mappings=validated_mappings,
        mapped_rows=mapped_rows,
        unmapped_source=unmapped_source,
        unmapped_target=unmapped_target,
        metadata={
            "selected_sheet": selected_sheet,
            "mapping_mode": "agent1_json",
            "sample_only": bool(raw_sample_rows),
            "total_source_columns": len(source_columns),
            "total_mapped_targets": len(mapped_target_fields),
            "llm_used": llm_adapter is not None,
        },
    )


# ---------------------------------------------------------------------------
# SchemaMappingAgent — shared pipeline interface
# ---------------------------------------------------------------------------

class SchemaMappingAgent:
    """
    Agent 2: Maps source workbook column headers to the canonical 17 SOV schema fields.

    Consumes the output of Agent 1 through the shared SOVProcessingState.
    Produces SchemaMapping objects in state.schema_mappings.

    Respects human-in-the-loop boundary:
    - Does NOT make final data changes.
    - Marks each mapping as approved / needs_review / rejected.
    - Human Review reads status and decides whether to accept or override.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        llm_adapter: Optional[LLMAdapter] = None,
    ):
        self.model_name = model_name or os.getenv("SOV_LLM_MODEL", "gpt-4o")
        self._llm_adapter = llm_adapter  # injectable for testing

    def run(self, state: SOVProcessingState) -> SOVProcessingState:
        """
        Execute schema mapping on the selected sheet.

        Reads source column names from:
          1. state.metadata["raw_columns"]  — preferred (set by Agent 1 or ingestion)
          2. state.metadata["agent1_output"] — full Agent 1 JSON contract
          3. Falls back to placeholder if neither is available.

        Writes to:
          state.schema_mappings
          state.metadata["unmapped_source_columns"]
          state.metadata["missing_target_fields"]
          state.metadata["mapping_report"]
        """
        # Resolve source columns from state
        raw_columns: Optional[list[str]] = state.metadata.get("raw_columns")
        agent1_output: Optional[dict[str, Any]] = state.metadata.get("agent1_output")
        agent1_suggestions: dict[str, dict] = state.metadata.get("agent1_suggestions", {})

        if agent1_output and isinstance(agent1_output, dict):
            # Full Agent 1 JSON contract available
            try:
                result = map_agent1_output(agent1_output, llm_adapter=self._llm_adapter)
                mappings = result.mappings
                unmapped_source = result.unmapped_source
                unmapped_target = result.unmapped_target
                # Store mapped rows in metadata for Agent 3 consumption
                state.metadata["mapped_rows"] = result.mapped_rows
                state.metadata["mapping_report"] = result.metadata
            except Exception as e:
                logger.error(f"SchemaMappingAgent: map_agent1_output failed: {e}")
                state.errors.append(f"Schema mapping error: {e}")
                state.status = JobStatus.SCHEMA_MAPPED
                return state

        elif raw_columns and isinstance(raw_columns, list):
            # Flat column list available
            raw_mappings = [
                _map_single_column_internal(
                    source_col=col,
                    agent1_suggestion=agent1_suggestions.get(col),
                    llm_adapter=self._llm_adapter,
                )
                for col in raw_columns
            ]
            mappings = _validate_and_resolve_conflicts(raw_mappings)
            unmapped_source = [
                m.source_column for m in mappings
                if m.status == _STATUS_REJECTED or m.target_field is None
            ]
            mapped_target_fields = {
                m.target_field for m in mappings
                if m.target_field and m.status != _STATUS_REJECTED
            }
            unmapped_target = [f for f in CANONICAL_SOV_FIELDS if f not in mapped_target_fields]
            state.metadata["unmapped_source_columns"] = unmapped_source
            state.metadata["missing_target_fields"] = unmapped_target
            state.metadata["mapping_report"] = {
                "total_source_columns": len(raw_columns),
                "total_mapped_targets": len(mapped_target_fields),
            }

        else:
            # No source columns available — log and return placeholder compatible output
            logger.warning(
                "SchemaMappingAgent: No source columns found in state. "
                "Set state.metadata['raw_columns'] or state.metadata['agent1_output']."
            )
            # Keep any existing placeholder mappings
            state.status = JobStatus.SCHEMA_MAPPED
            return state

        state.schema_mappings = mappings
        state.metadata["unmapped_source_columns"] = unmapped_source
        state.metadata["missing_target_fields"] = unmapped_target
        state.status = JobStatus.SCHEMA_MAPPED
        return state
