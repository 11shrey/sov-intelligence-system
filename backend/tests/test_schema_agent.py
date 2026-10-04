"""
Integrated tests for Agent 2 (Schema Mapping) — adapted for the shared repository.

Tests the real implementation in app/agents/schema_agent.py using the shared
Pydantic contracts from app/models/schema_models.py.

Coverage:
  - Exact column match
  - Alias match (curated domain aliases)
  - Normalised / fuzzy match
  - Low-confidence mapping
  - Unmapped column handling
  - Confidence score ranges
  - Standard 17-field target mapping
  - TIV isolation safety
  - Geographic boundary protection
  - Duplicate target conflict resolution
  - LLM fallback routing & mock testing
  - Canonical 17-field output ordering (C-03)
  - Input immutability (C-01)
  - Zero hallucination of missing fields (C-02)
  - Agent 1 JSON contract integration
  - SchemaMappingAgent pipeline integration
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path
from typing import Any

import pytest

# The shared repo uses pythonpath = . in pytest.ini so imports are relative to backend/
from app.agents.schema_agent import (
    CANONICAL_SOV_FIELDS,
    LLMAdapter,
    map_agent1_output,
    map_columns,
    map_schema,
    map_single_column,
    _CONFIDENCE_APPROVED,
    _CONFIDENCE_REVIEW,
    _STATUS_APPROVED,
    _STATUS_NEEDS_REVIEW,
    _STATUS_REJECTED,
)
from app.models.schema_models import (
    SchemaMapping,
    SchemaMappingReport,
    TARGET_SOV_FIELDS,
    TargetSOVField,
)
from app.agents.schema_agent import SchemaMappingAgent
from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_with_columns(cols: list[str]) -> SOVProcessingState:
    fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
    state = SOVProcessingState(job_id="test-job", file_info=fi)
    state.metadata["raw_columns"] = cols
    return state


# ===========================================================================
# 1. Canonical fields check
# ===========================================================================

class TestCanonicalFields:

    def test_canonical_fields_count(self):
        assert len(CANONICAL_SOV_FIELDS) == 17

    def test_canonical_fields_match_target_sov_fields(self):
        assert CANONICAL_SOV_FIELDS == TARGET_SOV_FIELDS

    def test_all_canonical_fields_present(self):
        expected = [
            "Reference", "Address", "City", "State", "Zip", "County", "Country",
            "Building Value", "Contents", "BI", "Occupancy", "Construction",
            "Storeys", "Number of Buildings", "Year Built",
            "Fire Sprinklers (Y/N)", "Other",
        ]
        assert CANONICAL_SOV_FIELDS == expected


# ===========================================================================
# 2. Exact column match
# ===========================================================================

class TestExactMatch:

    @pytest.mark.parametrize("field", CANONICAL_SOV_FIELDS)
    def test_exact_match_all_17_fields(self, field: str):
        mapping = map_single_column(field)
        assert mapping.target_field == field
        assert mapping.confidence == 1.0
        assert mapping.method == "exact"
        assert mapping.status == _STATUS_APPROVED

    def test_exact_match_does_not_call_llm(self):
        called = []

        def mock_llm(payload):
            called.append(payload)
            return {"target_field": "Reference", "confidence": 0.9, "reasoning": "LLM"}

        adapter = LLMAdapter(llm_callable=mock_llm)
        result = map_single_column("Reference", llm_adapter=adapter)
        assert not called, "LLM was incorrectly called for an exact match"
        assert result.status == _STATUS_APPROVED


# ===========================================================================
# 3. Alias match (curated domain aliases)
# ===========================================================================

class TestAliasMatch:

    @pytest.mark.parametrize("source_col, expected_target", [
        ("property_id", "Reference"),
        ("street_address", "Address"),
        ("city_name", "City"),
        ("state_code", "State"),
        ("postal_code", "Zip"),
        ("county_name", "County"),
        ("country_name", "Country"),
        ("building_insured_value", "Building Value"),
        ("contents_value", "Contents"),
        ("business_income", "BI"),
        ("occupancy_type", "Occupancy"),
        ("construction_type", "Construction"),
        ("number_of_stories", "Storeys"),
        ("building_count", "Number of Buildings"),
        ("year_constructed", "Year Built"),
        ("sprinklers", "Fire Sprinklers (Y/N)"),
        ("other_value", "Other"),
        # Representative human-readable aliases
        ("Loc #", "Reference"),
        ("Street Address", "Address"),
        ("Bldg Repl Cost", "Building Value"),
        ("BI Limit", "BI"),
        ("Const Type", "Construction"),
        ("Yr Built", "Year Built"),
        ("Fire Prot.", "Fire Sprinklers (Y/N)"),
    ])
    def test_alias_mapping(self, source_col: str, expected_target: str):
        result = map_schema([{source_col: "sample_val"}])
        assert len(result.mappings) == 1
        m = result.mappings[0]
        assert m.target_field == expected_target, (
            f"Expected '{expected_target}' for alias '{source_col}', got '{m.target_field}'"
        )
        assert m.status == _STATUS_APPROVED
        assert m.confidence >= _CONFIDENCE_APPROVED


# ===========================================================================
# 4. Fuzzy match
# ===========================================================================

class TestFuzzyMatch:

    def test_material_maps_to_construction(self):
        mapping = map_single_column("material")
        assert mapping.target_field == "Construction"
        assert mapping.confidence >= _CONFIDENCE_APPROVED
        assert mapping.status in (_STATUS_APPROVED, _STATUS_NEEDS_REVIEW)

    def test_floor_count_maps_to_storeys(self):
        mapping = map_single_column("floor_count")
        assert mapping.target_field == "Storeys"
        assert mapping.confidence >= _CONFIDENCE_APPROVED

    def test_building_qty_maps_to_number_of_buildings(self):
        mapping = map_single_column("building_qty")
        assert mapping.target_field == "Number of Buildings"
        assert mapping.confidence >= _CONFIDENCE_APPROVED

    def test_street_location_maps_to_address(self):
        mapping = map_single_column("street_location")
        assert mapping.target_field == "Address"
        assert mapping.status in (_STATUS_APPROVED, _STATUS_NEEDS_REVIEW)


# ===========================================================================
# 5. Low-confidence / unmapped column handling
# ===========================================================================

class TestLowConfidenceAndUnmapped:

    def test_ambiguous_value_2_needs_review(self):
        result = map_schema([{"value_2": 1000}])
        m = result.mappings[0]
        assert m.status == _STATUS_NEEDS_REVIEW
        assert m.target_field is None
        assert m.confidence < _CONFIDENCE_REVIEW

    def test_unknown_column_rejected(self):
        result = map_schema([{"XYZZY_UNKNOWN_99": "abc"}])
        m = result.mappings[0]
        assert m.status in (_STATUS_REJECTED, _STATUS_NEEDS_REVIEW)
        assert m.target_field is None

    def test_empty_source_column_rejected(self):
        mapping = map_single_column("")
        assert mapping.target_field is None
        assert mapping.status == _STATUS_REJECTED
        assert mapping.confidence == 0.0


# ===========================================================================
# 6. Confidence score ranges
# ===========================================================================

class TestConfidenceScores:

    def test_exact_match_confidence_is_1(self):
        m = map_single_column("Reference")
        assert m.confidence == 1.0

    def test_alias_match_confidence_gte_085(self):
        m = map_single_column("postal_code")
        assert m.confidence >= _CONFIDENCE_APPROVED

    def test_rejected_mapping_confidence_is_low(self):
        result = map_schema([{"XYZZY_UNKNOWN_99": "abc"}])
        m = result.mappings[0]
        assert m.confidence < _CONFIDENCE_REVIEW


# ===========================================================================
# 7. Standard 17-field mapping — representative messy SOV
# ===========================================================================

class TestRepresentative17FieldMapping:

    def test_messy_sov_all_17_mapped(self):
        fixture_rows = [
            {
                "Loc #": "P-101",
                "Street Address": "100 Main St",
                "City": "Dallas",
                "ST": "TX",
                "Zip Code": "75001",
                "County": "Dallas",
                "Country": "USA",
                "Bldg Repl Cost": 2_500_000,
                "Contents": 400_000,
                "BI Limit": 100_000,
                "Occupancy Type": "Office",
                "Const Type": "Masonry",
                "Stories": 4,
                "Building Count": 1,
                "Yr Built": 2010,
                "Fire Prot.": "Y",
                "Other Value": 50_000,
            }
        ]
        result = map_schema(fixture_rows)
        assert len(result.mappings) == 17
        for m in result.mappings:
            assert m.status == _STATUS_APPROVED, (
                f"Expected approved for '{m.source_column}' -> '{m.target_field}', "
                f"got {m.status}: {m.reasoning}"
            )
        assert len(result.unmapped_target) == 0

    def test_canonical_17_fields_output_order(self):
        rows = [{"Reference": "LOC-1", "Building Value": 100_000}]
        result = map_schema(rows)
        assert list(result.mapped_rows[0].keys()) == CANONICAL_SOV_FIELDS

    def test_agent1_json_fixture_all_17_mapped(self):
        agent1_fixture = {
            "sheet_analysis": {
                "selected_sheet": "SOV",
                "sheets": [
                    {
                        "sheet_name": "SOV",
                        "sample_rows": [
                            [
                                "Reference", "Address", "City", "State", "Zip",
                                "County", "Country", "Building Value", "Contents",
                                "BI", "Occupancy", "Construction", "Storeys",
                                "Number of Buildings", "Year Built",
                                "Fire Sprinklers (Y/N)", "Other",
                            ],
                            [
                                "PROP-001", "742 Evergreen Terr", "Springfield",
                                "IL", "62704", "Sangamon", "USA",
                                "450000.0", "120000.0", "0.0",
                                "Residential", "Wood", "2", "1", "1994", "N", "15000.0",
                            ],
                        ],
                    }
                ],
            },
            "mappings": [],
        }
        result = map_agent1_output(agent1_fixture)
        assert len(result.mappings) == 17
        for m in result.mappings:
            assert m.status == _STATUS_APPROVED
            assert m.target_field in CANONICAL_SOV_FIELDS
            assert m.confidence >= _CONFIDENCE_APPROVED

        row = result.mapped_rows[0]
        assert row["Reference"] == "PROP-001"
        assert row["Building Value"] == "450000.0"
        assert row["Fire Sprinklers (Y/N)"] == "N"


# ===========================================================================
# 8. TIV isolation safety
# ===========================================================================

class TestTivSafety:

    @pytest.mark.parametrize("tiv_header", [
        "Total Insured Value", "TIV", "Total TIV", "Total Value",
    ])
    def test_tiv_does_not_map_to_building_value(self, tiv_header: str):
        result = map_schema([{tiv_header: 10_000_000}])
        m = result.mappings[0]
        assert m.target_field != "Building Value", (
            f"TIV header '{tiv_header}' was wrongly mapped to Building Value!"
        )
        assert m.target_field != "Contents"

    def test_tiv_rejected_even_with_llm(self):
        def mock_llm(payload):
            return {
                "target_field": "Building Value",
                "confidence": 0.99,
                "reasoning": "Forced TIV mapping",
                "status": "approved",
            }

        adapter = LLMAdapter(llm_callable=mock_llm)
        mapping = map_single_column("tiv", llm_adapter=adapter)
        assert mapping.target_field is None
        assert mapping.status == _STATUS_REJECTED
        assert mapping.confidence == 0.0


# ===========================================================================
# 9. Geographic boundary protection
# ===========================================================================

class TestGeographicSafety:

    @pytest.mark.parametrize("header, expected", [
        ("city_name", "City"),
        ("town", "City"),
        ("state_code", "State"),
        ("province", "State"),
        ("zip_code", "Zip"),
        ("postal_code", "Zip"),
        ("county_name", "County"),
        ("parish", "County"),
        ("country_name", "Country"),
        ("nation", "Country"),
    ])
    def test_geographic_fields_not_confused(self, header: str, expected: str):
        result = map_schema([{header: "val"}])
        m = result.mappings[0]
        assert m.target_field == expected, (
            f"Geographic header '{header}' mapped to '{m.target_field}', expected '{expected}'"
        )


# ===========================================================================
# 10. Duplicate target conflict resolution
# ===========================================================================

class TestDuplicateTargetConflict:

    def test_duplicate_target_conflict_detected(self):
        rows = [{"contents": 50_000, "contents_value": 60_000}]
        result = map_schema(rows)
        assert len(result.mappings) == 2
        for m in result.mappings:
            assert m.target_field == "Contents"
            assert m.status == _STATUS_NEEDS_REVIEW
            assert "CONFLICT" in m.reasoning

    def test_property_id_and_street_location_no_collision(self):
        agent1_input = {
            "sheet_analysis": {
                "selected_sheet": "test_sheet",
                "sheets": [
                    {
                        "sheet_name": "test_sheet",
                        "sample_rows": [
                            ["property_id", "street_location"],
                            ["PROP-101", "123 Market Street"],
                        ],
                    }
                ],
            },
            "mappings": [],
        }
        res = map_agent1_output(agent1_input)
        m_map = {m.source_column: m for m in res.mappings}
        assert m_map["property_id"].target_field == "Reference"
        assert m_map["street_location"].target_field == "Address"
        assert "CONFLICT" not in m_map["property_id"].reasoning
        assert "CONFLICT" not in m_map["street_location"].reasoning


# ===========================================================================
# 11. LLM fallback routing
# ===========================================================================

class TestLLMFallback:

    def test_exact_match_bypasses_llm(self):
        called = []

        def mock_llm(payload):
            called.append(payload)
            return {"target_field": "Reference", "confidence": 0.9, "reasoning": "LLM"}

        adapter = LLMAdapter(llm_callable=mock_llm)
        result = map_schema([{"Reference": "REF-1"}], llm_adapter=adapter)
        assert not called
        assert result.mappings[0].status == _STATUS_APPROVED

    def test_ambiguous_column_calls_llm(self):
        called = []

        def mock_llm(payload):
            called.append(payload)
            assert payload["source_column"] == "custom_building_purpose"
            return {
                "target_field": "Occupancy",
                "confidence": 0.94,
                "reasoning": "Describes use/purpose of building.",
                "status": "approved",
            }

        adapter = LLMAdapter(llm_callable=mock_llm)
        result = map_schema([{"custom_building_purpose": "Warehouse"}], llm_adapter=adapter)
        assert called
        m = result.mappings[0]
        assert m.target_field == "Occupancy"
        assert m.confidence == 0.94
        assert m.method == "llm"

    def test_llm_failure_safe_fallback(self):
        def failing_llm(payload):
            raise RuntimeError("API timeout")

        adapter = LLMAdapter(llm_callable=failing_llm)
        result = map_schema([{"ambiguous_col_xyz": 123}], llm_adapter=adapter)
        m = result.mappings[0]
        assert m.status in (_STATUS_NEEDS_REVIEW, _STATUS_REJECTED)
        assert m.confidence < _CONFIDENCE_REVIEW

    def test_llm_invalid_target_rejected(self):
        def mock_llm(payload):
            return {
                "target_field": "NonExistentField",
                "confidence": 0.99,
                "reasoning": "Invalid canonical field",
                "status": "approved",
            }

        adapter = LLMAdapter(llm_callable=mock_llm)
        mapping = map_single_column("custom_field_xyz", llm_adapter=adapter)
        assert mapping.target_field is None
        assert mapping.status == _STATUS_REJECTED

    def test_llm_result_always_needs_review(self):
        """LLM results must always be needs_review — never blindly auto-approved."""
        def mock_llm(payload):
            return {
                "target_field": "Building Value",
                "confidence": 0.85,
                "reasoning": "Structure replacement cost.",
                "status": "approved",  # LLM claims approved, Agent 2 must override
            }

        adapter = LLMAdapter(llm_callable=mock_llm)
        mapping = map_single_column("structure_cost", llm_adapter=adapter)
        assert mapping.target_field == "Building Value"
        assert mapping.method == "llm"
        assert mapping.status == _STATUS_NEEDS_REVIEW  # Agent 2 must enforce this


# ===========================================================================
# 12. Input immutability (C-01)
# ===========================================================================

class TestInputImmutability:

    def test_agent1_input_not_mutated(self):
        agent1_fixture = {
            "sheet_analysis": {
                "selected_sheet": "Sheet1",
                "sheets": [
                    {
                        "sheet_name": "Sheet1",
                        "sample_rows": [["Reference"], ["PROP-1"]],
                    }
                ],
            },
            "mappings": [],
        }
        original = copy.deepcopy(agent1_fixture)
        _ = map_agent1_output(agent1_fixture)
        assert agent1_fixture == original

    def test_raw_values_preserved_verbatim(self):
        rows = [{"Bldg Repl Cost": "$5,000,000"}]
        result = map_schema(rows)
        assert result.mapped_rows[0]["Building Value"] == "$5,000,000"


# ===========================================================================
# 13. Zero hallucination (C-02)
# ===========================================================================

class TestZeroHallucination:

    def test_missing_target_fields_are_none(self):
        rows = [{"Reference": "REF-1", "Building Value": 500_000}]
        result = map_schema(rows)
        assert "County" in result.unmapped_target
        assert result.mapped_rows[0]["County"] is None

    def test_unmapped_targets_reported(self):
        rows = [{"Reference": "REF-1"}]
        result = map_schema(rows)
        # Only Reference is mapped, all others should be unmapped
        assert "Building Value" in result.unmapped_target
        assert "Address" in result.unmapped_target


# ===========================================================================
# 14. SchemaMappingAgent pipeline integration
# ===========================================================================

class TestSchemaMappingAgentPipeline:

    def test_agent_instantiation(self):
        agent = SchemaMappingAgent()
        assert agent is not None

    def test_agent_run_with_raw_columns(self):
        state = _state_with_columns([
            "Loc #", "Street Address", "City", "ST", "Zip Code",
            "County", "Country", "Bldg Repl Cost", "Contents", "BI Limit",
            "Occupancy Type", "Const Type", "Stories", "Building Count",
            "Yr Built", "Fire Prot.", "Other Value",
        ])
        agent = SchemaMappingAgent()
        updated_state = agent.run(state)
        assert updated_state.status == JobStatus.SCHEMA_MAPPED
        assert len(updated_state.schema_mappings) == 17
        for m in updated_state.schema_mappings:
            assert m.status == _STATUS_APPROVED

    def test_agent_run_no_columns_safe(self):
        """Agent must not crash when no source columns are in state."""
        fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
        state = SOVProcessingState(job_id="test-job", file_info=fi)
        agent = SchemaMappingAgent()
        updated_state = agent.run(state)
        assert updated_state.status == JobStatus.SCHEMA_MAPPED

    def test_agent_run_with_agent1_json(self):
        fi = FileInfo(filename="test.xlsx", file_path="data/uploads/test.xlsx")
        state = SOVProcessingState(job_id="test-job", file_info=fi)
        state.metadata["agent1_output"] = {
            "sheet_analysis": {
                "selected_sheet": "SOV",
                "sheets": [
                    {
                        "sheet_name": "SOV",
                        "sample_rows": [
                            ["Reference", "Building Value"],
                            ["LOC-001", "1000000"],
                        ],
                    }
                ],
            },
            "mappings": [],
        }
        agent = SchemaMappingAgent()
        updated_state = agent.run(state)
        assert updated_state.status == JobStatus.SCHEMA_MAPPED
        assert len(updated_state.schema_mappings) >= 2
        targets = {m.target_field for m in updated_state.schema_mappings}
        assert "Reference" in targets
        assert "Building Value" in targets


# ===========================================================================
# 16. Value-Aware Evidence Tests
# ===========================================================================

class TestValueAwareEvidence:

    def test_floor_with_integers_confirms_storeys(self):
        rows = [{"#Floor": 2}, {"#Floor": 1}, {"#Floor": 4}]
        result = map_schema(rows)
        m = next(m for m in result.mappings if m.source_column == "#Floor")
        assert m.target_field == "Storeys"
        assert m.status == _STATUS_APPROVED
        assert m.confidence >= _CONFIDENCE_APPROVED
        assert "confirm floor/story" in m.reasoning

    def test_yr_built_with_four_digit_years_confirms_year_built(self):
        rows = [{"Yr. Built": "1990"}, {"Yr. Built": "1977"}, {"Yr. Built": "1965"}]
        result = map_schema(rows)
        m = next(m for m in result.mappings if m.source_column == "Yr. Built")
        assert m.target_field == "Year Built"
        assert m.status == _STATUS_APPROVED
        assert "confirm 4-digit construction years" in m.reasoning

    def test_construction_with_material_keywords_confirms_construction(self):
        rows = [{"Construction": "Masonry"}, {"Construction": "Steel Frame"}, {"Construction": "Frame"}]
        result = map_schema(rows)
        m = next(m for m in result.mappings if m.source_column == "Construction")
        assert m.target_field == "Construction"
        assert m.status == _STATUS_APPROVED

    def test_sprinklers_with_indicators_confirms_sprinklers(self):
        rows = [{"%Sprink": "Yes"}, {"%Sprink": "No"}, {"%Sprink": "100%"}]
        result = map_schema(rows)
        m = next(m for m in result.mappings if m.source_column == "%Sprink")
        assert m.target_field == "Fire Sprinklers (Y/N)"
        assert m.confidence >= 0.70

    def test_financial_value_with_monetary_floats_confirms_building_value(self):
        rows = [{"2023 Building Value": 1068367.75}, {"2023 Building Value": 10172.1}]
        result = map_schema(rows)
        m = next(m for m in result.mappings if m.source_column == "2023 Building Value")
        assert m.target_field == "Building Value"
        assert m.confidence >= 0.75


# ===========================================================================
# 17. Negative Evidence and Rejection Tests
# ===========================================================================

class TestNegativeEvidence:

    def test_roof_construction_rejected_from_construction(self):
        m = map_single_column("Roof Construction")
        assert m.target_field != "Construction"

    def test_reconstruction_date_rejected_from_year_built(self):
        m = map_single_column("Reconstruction Date")
        assert m.target_field != "Year Built"

    def test_valuation_year_rejected_from_year_built(self):
        m = map_single_column("Year of Marshall Swift Valution")
        assert m.target_field != "Year Built"

    def test_risk_assessment_year_rejected_from_year_built(self):
        m = map_single_column("Year of Property Risk Assement")
        assert m.target_field != "Year Built"

    def test_sq_ft_rejected_from_building_value(self):
        m = map_single_column("Sq. Ft. ")
        assert m.target_field != "Building Value"

    def test_total_isolated_from_financial_fields(self):
        m = map_single_column("2023 TOTAL")
        assert m.target_field not in ("Building Value", "Contents", "BI", "Other")


# ===========================================================================
# 18. Confidence Margin Tests
# ===========================================================================

class TestConfidenceMargin:

    def test_ambiguous_column_routes_to_needs_review(self):
        m = map_single_column("value_2")
        assert m.status == _STATUS_NEEDS_REVIEW

