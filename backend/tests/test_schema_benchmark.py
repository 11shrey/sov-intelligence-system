"""
Reproducible Benchmark Test for Agent 2 (Schema Mapping).

Measures and asserts:
1. Mapping Precision: Correctly Mapped / (Correctly Mapped + Incorrectly Mapped)
2. Supported Schema Coverage: Correctly Mapped / Physically Present Target Fields
3. Full Schema Completion: Correctly Mapped / 17 Canonical Fields
4. Safety Violations: Count of unauthorized/hallucinated/conflicted mappings

Evaluated against:
- Benchmark A: Real-world SOV handoff fixture (SOV_Q8B3.xlsx, 12 supported fields, 5 legitimately absent)
- Benchmark B: Full 17-field messy insurance SOV fixture with real-world distractors
"""

import json
from pathlib import Path
import pytest
from app.agents.schema_agent import (
    SchemaMappingAgent,
    map_agent1_output,
    CANONICAL_SOV_FIELDS,
    _STATUS_APPROVED,
    _STATUS_REJECTED,
    _STATUS_NEEDS_REVIEW,
)
from app.orchestration.state import SOVProcessingState, FileInfo

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def calculate_benchmark_metrics(
    mapping_list: list,
    ground_truth_supported: dict,
    forbidden_mappings: dict = None,
):
    """
    Computes standard benchmark metrics.
    
    mapping_list: list of SchemaMapping objects
    ground_truth_supported: dict mapping source_column -> expected_target_field
    forbidden_mappings: dict mapping source_column -> forbidden_target_field
    """
    # Active mapped targets (excluding rejected)
    active_mappings = {
        m.source_column: m.target_field
        for m in mapping_list
        if m.status != _STATUS_REJECTED and m.target_field is not None
    }
    
    # All non-null targets for safety checking
    all_assigned_targets = {
        m.source_column: m.target_field
        for m in mapping_list
        if m.target_field is not None
    }
    
    correctly_mapped = 0
    incorrectly_mapped = 0
    safety_violations = 0
    
    # Check mappings for supported columns
    for src_col, expected_target in ground_truth_supported.items():
        mapped_target = active_mappings.get(src_col)
        if mapped_target == expected_target:
            correctly_mapped += 1
        elif mapped_target is not None:
            incorrectly_mapped += 1

    # Check forbidden mappings / safety violations
    if forbidden_mappings:
        for src_col, forbidden_target in forbidden_mappings.items():
            mapped_target = all_assigned_targets.get(src_col)
            # If forbidden target was assigned and not rejected, it's a critical safety violation
            if mapped_target == forbidden_target and active_mappings.get(src_col) == forbidden_target:
                safety_violations += 1

    total_attempted = correctly_mapped + incorrectly_mapped
    precision = (correctly_mapped / total_attempted * 100.0) if total_attempted > 0 else 0.0
    supported_coverage = (correctly_mapped / len(ground_truth_supported) * 100.0) if ground_truth_supported else 0.0
    full_completion = (correctly_mapped / len(CANONICAL_SOV_FIELDS) * 100.0)
    
    return {
        "correctly_mapped": correctly_mapped,
        "incorrectly_mapped": incorrectly_mapped,
        "supported_fields_count": len(ground_truth_supported),
        "total_canonical_fields": len(CANONICAL_SOV_FIELDS),
        "safety_violations": safety_violations,
        "mapping_precision_pct": round(precision, 2),
        "supported_coverage_pct": round(supported_coverage, 2),
        "full_completion_pct": round(full_completion, 2),
    }


class TestSchemaMappingBenchmark:
    """Reproducible benchmark suite for Agent 2."""

    def test_benchmark_real_sov_q8b3(self):
        """
        Benchmark A: Real-world municipal SOV (SOV_Q8B3).
        Source file has 12 physically present canonical fields.
        5 fields (City, State, Country, Number of Buildings, Other) are absent from the document.
        Under C-01 and C-02, missing fields MUST remain None (0 hallucinations).
        """
        fixture_path = FIXTURES_DIR / "agent1_handoff_SOV_Q8B3.json"
        assert fixture_path.exists(), f"Fixture missing: {fixture_path}"

        with open(fixture_path, "r", encoding="utf-8") as f:
            agent1_json = json.load(f)

        result = map_agent1_output(agent1_json)

        # Ground truth for physical fields present in SOV_Q8B3
        ground_truth = {
            "Address": "Address",
            "Zip": "Zip",
            "County": "County",
            "Yr. Built": "Year Built",
            "#Floor": "Storeys",
            "Construction": "Construction",
            "%Sprink": "Fire Sprinklers (Y/N)",
            "2023 Building Value": "Building Value",
            "2023 Contents Value": "Contents",
            "BI Value": "BI",
            "Complex/Facility": "Occupancy",
            "SW": "Reference",
        }

        forbidden = {
            "Roof Construction": "Construction",
            "Reconstruction Date": "Year Built",
            "Year of Property Risk Assement": "Year Built",
            "Year of Marshall Swift Valution": "Year Built",
            "Sq. Ft. ": "Building Value",
            "2023 TOTAL": "Building Value",
            "Loc #": "Reference",  # 100% empty ghost column must be rejected in conflict
        }

        metrics = calculate_benchmark_metrics(result.mappings, ground_truth, forbidden)

        # Assertions
        assert metrics["safety_violations"] == 0, f"Safety violations detected: {metrics['safety_violations']}"
        assert metrics["mapping_precision_pct"] == 100.0, f"Precision was {metrics['mapping_precision_pct']}%, expected 100.0%"
        assert metrics["supported_coverage_pct"] == 100.0, f"Supported coverage was {metrics['supported_coverage_pct']}%, expected 100.0%"
        assert metrics["full_completion_pct"] == 70.59, f"Completion was {metrics['full_completion_pct']}%, expected 70.59%"
        assert metrics["correctly_mapped"] == 12

        # Verify C-02: Zero hallucinated values for the 5 absent fields
        mapped_targets = {m.target_field for m in result.mappings if m.status != _STATUS_REJECTED and m.target_field}
        absent_fields = ["City", "State", "Country", "Number of Buildings", "Other"]
        for absent in absent_fields:
            assert absent not in mapped_targets, f"Field '{absent}' was hallucinated!"

        # Also verify through SchemaMappingAgent pipeline runner
        file_info = FileInfo(filename="SOV_Q8B3.xlsx", file_path="SOV_Q8B3.xlsx", file_size_bytes=1024)
        state = SOVProcessingState(job_id="benchmark_run_1", file_info=file_info)
        state.metadata["agent1_output"] = agent1_json
        agent = SchemaMappingAgent()
        out_state = agent.run(state)
        assert len(out_state.schema_mappings) > 0

    def test_benchmark_full_17_field_messy_sov(self):
        """
        Benchmark B: Messy SOV with full evidence for all 17 canonical fields plus distractors.
        Tests mapping accuracy and precision when source evidence is completely present.
        Target: >= 77% (here achieving 100% on supported fields).
        """
        full_agent1_input = {
            "job_id": "job_benchmark_17",
            "source_file": "comprehensive_messy_sov.xlsx",
            "raw_headers": [
                "Policy_Ref",
                "Street Loc",
                "Town",
                "State Prov",
                "Postal Code",
                "Parish",
                "Nation",
                "Bldg Repl Cost",
                "Contents Val",
                "BI Limit",
                "Property Use",
                "Const Type",
                "#Floor",
                "Bldg Count",
                "Yr. Built",
                "%Sprink",
                "Other Value",
                # Distractors / Negative cases
                "Roof Construction",
                "Sq. Ft.",
                "Total Insured Value",
                "Reconstruction Date",
                "Dept",
            ],
            "sample_rows": [
                [
                    "REF-001",
                    "100 Main St",
                    "Austin",
                    "TX",
                    "78701",
                    "Travis",
                    "USA",
                    1500000.0,
                    250000.0,
                    50000.0,
                    "Commercial Office",
                    "Masonry",
                    3,
                    1,
                    1995,
                    "Yes",
                    10000.0,
                    "Asphalt Shingle",
                    12000,
                    1810000.0,
                    2010,
                    "Admin",
                ]
            ],
        }

        result = map_agent1_output(full_agent1_input)

        ground_truth = {
            "Policy_Ref": "Reference",
            "Street Loc": "Address",
            "Town": "City",
            "State Prov": "State",
            "Postal Code": "Zip",
            "Parish": "County",
            "Nation": "Country",
            "Bldg Repl Cost": "Building Value",
            "Contents Val": "Contents",
            "BI Limit": "BI",
            "Property Use": "Occupancy",
            "Const Type": "Construction",
            "#Floor": "Storeys",
            "Bldg Count": "Number of Buildings",
            "Yr. Built": "Year Built",
            "%Sprink": "Fire Sprinklers (Y/N)",
            "Other Value": "Other",
        }

        forbidden = {
            "Roof Construction": "Construction",
            "Sq. Ft.": "Building Value",
            "Total Insured Value": "Building Value",
            "Reconstruction Date": "Year Built",
        }

        metrics = calculate_benchmark_metrics(result.mappings, ground_truth, forbidden)

        assert metrics["safety_violations"] == 0
        assert metrics["mapping_precision_pct"] == 100.0
        assert metrics["supported_coverage_pct"] == 100.0
        assert metrics["full_completion_pct"] == 100.0
        assert metrics["correctly_mapped"] == 17
