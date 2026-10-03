"""Focused unit tests for Agent 1 Semantic Concept Detection Engine.

Validates alias detection, false-positive protection, word boundary safety,
ambiguity handling, row-level analysis, and concept diversity scoring.
"""

from pathlib import Path
import pytest

from app.agents.sheet_intelligence.ingestion import UniversalIngestor
from app.agents.sheet_intelligence.semantics import SemanticDetector


@pytest.fixture
def detector() -> SemanticDetector:
    return SemanticDetector()


# =====================================================================
# 1. False Positive Protection Tests (Section 13)
# =====================================================================


def test_statement_does_not_match_state(detector: SemanticDetector):
    """'Statement' must NOT match 'state'."""
    detection = detector.detect_cell("Statement")
    assert not any(mc.concept == "state" for mc in detection.matched_concepts)

    detection_sov = detector.detect_cell("Statement of Values")
    assert not any(
        mc.concept == "state" for mc in detection_sov.matched_concepts
    )


def test_coverage_does_not_match_cover(detector: SemanticDetector):
    """'Coverage' must NOT match 'cover'."""
    detection = detector.detect_cell("Coverage")
    assert len(detection.matched_concepts) == 0


def test_building_alone_does_not_become_building_value(
    detector: SemanticDetector,
):
    """'Building' alone should NOT be mapped to 'val_bldg'."""
    detection = detector.detect_cell("Building")
    assert not any(mc.concept == "val_bldg" for mc in detection.matched_concepts)
    assert detection.is_ambiguous is True
    assert any(
        mc.concept == "building_signal" for mc in detection.matched_concepts
    )


def test_value_alone_does_not_become_building_value(
    detector: SemanticDetector,
):
    """'Value' alone should NOT be mapped to 'val_bldg' or 'val_tiv'."""
    detection = detector.detect_cell("Value")
    assert not any(mc.concept == "val_bldg" for mc in detection.matched_concepts)
    assert not any(mc.concept == "val_tiv" for mc in detection.matched_concepts)
    assert detection.is_ambiguous is True
    assert any(mc.concept == "value_signal" for mc in detection.matched_concepts)


def test_cost_alone_does_not_become_building_value(
    detector: SemanticDetector,
):
    """'Cost' alone should NOT be mapped to 'val_bldg'."""
    detection = detector.detect_cell("Cost")
    assert not any(mc.concept == "val_bldg" for mc in detection.matched_concepts)
    assert detection.is_ambiguous is True
    assert any(mc.concept == "value_signal" for mc in detection.matched_concepts)


def test_site_is_not_automatically_mapped_to_address(
    detector: SemanticDetector,
):
    """'Site' alone must NOT be forced into 'addr'; it provides an ambiguous location signal."""
    detection = detector.detect_cell("Site")
    assert not any(mc.concept == "addr" for mc in detection.matched_concepts)
    assert detection.is_ambiguous is True
    assert any(
        mc.concept == "location_signal" for mc in detection.matched_concepts
    )


def test_location_is_not_automatically_mapped_to_reference(
    detector: SemanticDetector,
):
    """'Location' alone must NOT be forced into 'ref'; it provides an ambiguous location signal."""
    detection = detector.detect_cell("Location")
    assert not any(mc.concept == "ref" for mc in detection.matched_concepts)
    assert detection.is_ambiguous is True
    assert any(
        mc.concept == "location_signal" for mc in detection.matched_concepts
    )


def test_case_insensitivity(detector: SemanticDetector):
    """Case variations must yield the exact same concept detections."""
    d1 = detector.detect_cell("BUILDING VALUE")
    d2 = detector.detect_cell("Building Value")
    d3 = detector.detect_cell("building value")

    assert [mc.concept for mc in d1.matched_concepts] == ["val_bldg"]
    assert [mc.concept for mc in d2.matched_concepts] == ["val_bldg"]
    assert [mc.concept for mc in d3.matched_concepts] == ["val_bldg"]


def test_whitespace_and_punctuation_normalization(detector: SemanticDetector):
    """Punctuation noise ($), (#), underscores, and extra spaces must not prevent matching."""
    d1 = detector.detect_cell("  Building   Value  ($) ")
    assert any(mc.concept == "val_bldg" for mc in d1.matched_concepts)

    d2 = detector.detect_cell("Ref #")
    assert any(mc.concept == "ref" for mc in d2.matched_concepts)

    d3 = detector.detect_cell("Loc_ID")
    assert any(mc.concept == "ref" for mc in d3.matched_concepts)


# =====================================================================
# 2. Positive Detection Tests (Section 14)
# =====================================================================


@pytest.mark.parametrize(
    "raw_input,expected_concept",
    [
        ("Reference", "ref"),
        ("Loc ID", "ref"),
        ("Ref No", "ref"),
        ("Property ID", "ref"),
        ("Location Number", "ref"),
        ("Street Address", "addr"),
        ("Property Address", "addr"),
        ("Mailing Address", "addr"),
        ("City", "city"),
        ("Municipality", "city"),
        ("State", "state"),
        ("Province", "state"),
        ("Postal Code", "zip"),
        ("Zipcode", "zip"),
        ("Zip Code", "zip"),
        ("County", "county"),
        ("Country", "country"),
        ("Building Value", "val_bldg"),
        ("Building Cost", "val_bldg"),
        ("Structure Value", "val_bldg"),
        ("Bldg Cost", "val_bldg"),
        ("Contents", "val_cont"),
        ("Contents Value", "val_cont"),
        ("BPP", "val_cont"),
        ("Business Personal Property", "val_cont"),
        ("BI", "val_bi"),
        ("Business Interruption", "val_bi"),
        ("Time Element", "val_bi"),
        ("TIV", "val_tiv"),
        ("Total Insured Value", "val_tiv"),
        ("Occupancy", "occ"),
        ("Occupancy Type", "occ"),
        ("Tenant", "occ"),
        ("Property Use", "occ"),
        ("Construction", "const"),
        ("Construction Type", "const"),
        ("Stories", "stories"),
        ("Number of Stories", "stories"),
        ("Number of Floors", "stories"),
        ("Year Built", "yr_built"),
        ("Construction Year", "yr_built"),
        ("Sprinkler", "sprinkler"),
        ("Fire Sprinklers", "sprinkler"),
        ("Sprinklered", "sprinkler"),
    ],
)
def test_positive_concept_detections(
    detector: SemanticDetector, raw_input: str, expected_concept: str
):
    detection = detector.detect_cell(raw_input)
    matched_ids = [mc.concept for mc in detection.matched_concepts]
    assert (
        expected_concept in matched_ids
    ), f"Expected '{expected_concept}' in {matched_ids} for input '{raw_input}'"
    assert detection.is_ambiguous is False


# =====================================================================
# 3. Row-Level Analysis & Distinct Concept Scoring (Section 11 & 12)
# =====================================================================


def test_distinct_concept_scoring_diversity(detector: SemanticDetector):
    """Verify that multiple aliases for 1 concept score lower than diverse concepts."""
    # Row A: 4 aliases all meaning 'addr'
    redundant_row = [
        "Address",
        "Street Address",
        "Property Address",
        "Mailing Address",
    ]
    res_redundant = detector.analyze_row(redundant_row, row_index=0)

    assert res_redundant.concept_count == 1
    assert res_redundant.distinct_concepts == ["addr"]
    assert res_redundant.diversity_score == round(1.0 / 7.0, 3)

    # Row B: 7 diverse core concepts
    diverse_row = [
        "Reference",
        "Street Address",
        "City",
        "State",
        "Zip",
        "Building Cost",
        "Occupancy",
    ]
    res_diverse = detector.analyze_row(diverse_row, row_index=4)

    assert res_diverse.concept_count == 7
    assert res_diverse.distinct_concepts == [
        "addr",
        "city",
        "occ",
        "ref",
        "state",
        "val_bldg",
        "zip",
    ]
    assert res_diverse.diversity_score == 1.0


def test_row_level_preservation_of_raw_cells(detector: SemanticDetector):
    """RowDetection must strictly preserve the raw cells and indices."""
    raw_cells = [
        "Ref #",
        "Site",
        "Building Cost ($)",
        "BI",
        "Occupancy Description",
    ]
    res = detector.analyze_row(raw_cells, row_index=2)

    assert res.row_index == 2
    assert res.raw_cells == raw_cells
    assert len(res.cell_detections) == 5

    # Check cell 0: Ref #
    assert res.cell_detections[0].raw_text == "Ref #"
    assert res.cell_detections[0].normalized_text == "ref"

    # Check cell 1: Site (ambiguous)
    assert res.cell_detections[1].raw_text == "Site"
    assert res.cell_detections[1].is_ambiguous is True
    assert "location_signal" in res.ambiguous_signals

    # Check cell 2: Building Cost ($)
    assert res.cell_detections[2].raw_text == "Building Cost ($)"
    assert any(
        mc.concept == "val_bldg"
        for mc in res.cell_detections[2].matched_concepts
    )


# =====================================================================
# 4. Integration with Universal Ingestion Layer (Section 18)
# =====================================================================


def test_integration_with_universal_ingestion(
    tmp_path: Path, detector: SemanticDetector
):
    """Verify SemanticDetector consumes the normalized output of UniversalIngestor."""
    csv_file = tmp_path / "integration.csv"
    csv_content = (
        "Brokerage Submission Banner\n"
        "\n"
        "Loc ID,Street Address,City,State,Zip Code,Building Cost,Contents,BI,Occupancy\n"
        "001,100 Main St,Austin,TX,78701,15000000,2000000,1000000,Office\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    ingestor = UniversalIngestor()
    workbook = ingestor.ingest(csv_file)
    grid = workbook.tables["default"]

    # Banner Row (Row 0)
    res_row0 = detector.analyze_row(grid.matrix[0], row_index=0)
    assert res_row0.concept_count == 0
    assert res_row0.diversity_score == 0.0

    # Blank Row (Row 1)
    res_row1 = detector.analyze_row(grid.matrix[1], row_index=1)
    assert res_row1.concept_count == 0

    # Header Row (Row 2)
    res_row2 = detector.analyze_row(grid.matrix[2], row_index=2)
    assert res_row2.concept_count >= 8
    assert res_row2.diversity_score == 1.0
    assert set(res_row2.distinct_concepts) >= {
        "ref",
        "addr",
        "city",
        "state",
        "zip",
        "val_bldg",
        "val_cont",
        "val_bi",
        "occ",
    }
