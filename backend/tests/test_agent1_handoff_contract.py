"""Focused tests for Agent 1 -> Agent 2 Handoff JSON Contract.

Validates Pydantic schema validation, deterministic JSON serialization,
null/no-detection behavior, raw data preservation, and the explicit Agent 2 boundary
(proving Agent 1 does NOT perform canonical schema mapping).
"""

from pathlib import Path
import json
import openpyxl
import pytest
from pydantic import ValidationError

from app.agents.sheet_intelligence.agent import SheetIntelligenceEngine
from app.agents.sheet_intelligence.contracts import (
    Agent1HandoffResult,
    SemanticEvidenceItem,
    SheetEvaluationAudit,
)


@pytest.fixture
def engine() -> SheetIntelligenceEngine:
    return SheetIntelligenceEngine()


# =====================================================================
# 1, 4. Successful XLSX Result & Multi-Sheet Evaluation
# =====================================================================


def test_successful_xlsx_handoff(tmp_path: Path, engine: SheetIntelligenceEngine):
    """Test 1 & 4: Successful multi-sheet XLSX evaluated and packaged into Agent1HandoffResult."""
    file_path = tmp_path / "multi_tab_sov.xlsx"
    wb = openpyxl.Workbook()

    ws_cover = wb.active
    ws_cover.title = "Instructions"
    ws_cover.append(["Submission Guide: Fill in all rows."])

    ws_sov = wb.create_sheet(title="Property Schedule")
    ws_sov.append(["Acme Brokerage Corp"])
    ws_sov.append(["Date: 2026-10-01"])
    ws_sov.append([])
    ws_sov.append(
        [
            "Loc ID",
            "Street Address",
            "City",
            "State",
            "Zip",
            "Building Cost ($)",
            "Occupancy",
        ]
    )
    for i in range(1, 11):
        ws_sov.append(
            [
                f"P{i:03d}",
                f"{i * 100} Main St",
                "Chicago",
                "IL",
                "60601",
                f"{i * 1000000}",
                "Office",
            ]
        )

    wb.save(file_path)

    result = engine.process(file_path=file_path, job_id="job_xlsx_001")

    assert isinstance(result, Agent1HandoffResult)
    assert result.job_id == "job_xlsx_001"
    assert result.source_file == "multi_tab_sov.xlsx"
    assert result.file_type == "xlsx"
    assert result.selected_sheet == "Property Schedule"
    assert result.header_row == 3
    assert result.confidence >= 0.85

    # Check total_rows: 10 data records beneath header
    assert result.total_rows == 10

    # Check sample_rows: 5 default sample rows
    assert len(result.sample_rows) == 5
    assert result.sample_rows[0] == [
        "P001",
        "100 Main St",
        "Chicago",
        "IL",
        "60601",
        "1000000",
        "Office",
    ]

    # Check candidate evaluation audit
    assert len(result.all_sheets_evaluated) == 2
    sheet_names = [s.sheet_name for s in result.all_sheets_evaluated]
    assert "Instructions" in sheet_names
    assert "Property Schedule" in sheet_names


# =====================================================================
# 2. Successful CSV Result
# =====================================================================


def test_successful_csv_handoff(tmp_path: Path, engine: SheetIntelligenceEngine):
    """Test 2: Successful CSV file handoff."""
    file_path = tmp_path / "locations.csv"
    csv_content = (
        "Loc ID,Street Address,City,State,Zip,Building Cost,Occupancy\n"
        "LOC-1,100 Broad St,New York,NY,10004,15000000,Commercial Office\n"
        "LOC-2,200 Broad St,New York,NY,10005,25000000,Commercial Office\n"
    )
    file_path.write_text(csv_content, encoding="utf-8")

    result = engine.process(file_path=file_path, job_id="job_csv_002")

    assert result.selected_sheet == "default"
    assert result.header_row == 0
    assert result.total_rows == 2
    assert len(result.sample_rows) == 2
    assert result.raw_headers == [
        "Loc ID",
        "Street Address",
        "City",
        "State",
        "Zip",
        "Building Cost",
        "Occupancy",
    ]


# =====================================================================
# 3. Successful JSON Result
# =====================================================================


def test_successful_json_handoff(tmp_path: Path, engine: SheetIntelligenceEngine):
    """Test 3: Successful JSON file handoff."""
    file_path = tmp_path / "schedule.json"
    json_content = """[
        {"Ref": "R1", "Location": "100 Pine", "City": "Seattle", "State": "WA", "Building Value": 5000000, "Occupancy": "Retail"},
        {"Ref": "R2", "Location": "200 Pine", "City": "Seattle", "State": "WA", "Building Value": 8000000, "Occupancy": "Office"}
    ]"""
    file_path.write_text(json_content, encoding="utf-8")

    result = engine.process(file_path=file_path, job_id="job_json_003")

    assert result.selected_sheet == "default"
    assert result.header_row == 0
    assert result.total_rows == 2
    assert result.raw_headers == [
        "Ref",
        "Location",
        "City",
        "State",
        "Building Value",
        "Occupancy",
    ]


# =====================================================================
# 5. No Valid SOV Table Result
# =====================================================================


def test_no_valid_sov_table_result(
    tmp_path: Path, engine: SheetIntelligenceEngine
):
    """Test 5: File with no valid SOV table produces a valid 'not detected' contract."""
    file_path = tmp_path / "readme.csv"
    file_path.write_text(
        "Notice\nThis is not a property schedule.\nPlease refer to email.\n",
        encoding="utf-8",
    )

    result = engine.process(file_path=file_path, job_id="job_fail_004")

    assert result.selected_sheet is None
    assert result.header_row is None
    assert result.confidence == 0.0
    assert result.raw_headers == []
    assert result.sample_rows == []
    assert result.total_rows == 0
    assert len(result.all_sheets_evaluated) >= 1
    assert any("No sheet qualified" in r for r in result.reasoning)


# =====================================================================
# 6, 7, 8, 9. Raw Headers & Sample Values Preservation
# =====================================================================


def test_raw_headers_and_sample_values_preserved_verbatim(
    tmp_path: Path, engine: SheetIntelligenceEngine
):
    """Test 6, 7, 8, 9: Header text and sample records are not altered, cleaned, or renamed."""
    file_path = tmp_path / "raw_preserve.csv"
    file_path.write_text(
        " Loc ID ,Street Address,Building Cost ($),Occ.\n"
        '001,100 Main St,"$1,500,000",Office\n'
        '002,200 Main St,"$2,500,000",Retail\n',
        encoding="utf-8",
    )

    result = engine.process(file_path=file_path, job_id="job_raw_005")

    # Header preservation: exact whitespace and punctuation
    assert result.raw_headers == [
        " Loc ID ",
        "Street Address",
        "Building Cost ($)",
        "Occ.",
    ]

    # Sample values preservation: strings and currency formatting preserved
    assert result.sample_rows[0] == ["001", "100 Main St", "$1,500,000", "Office"]
    assert result.sample_rows[1] == ["002", "200 Main St", "$2,500,000", "Retail"]
    assert result.total_rows == 2


# =====================================================================
# 11. Semantic Evidence Structure
# =====================================================================


def test_semantic_evidence_structure(
    tmp_path: Path, engine: SheetIntelligenceEngine
):
    """Test 11: Semantic evidence is provided per raw column without final schema mapping."""
    file_path = tmp_path / "evidence.csv"
    file_path.write_text(
        "Site,Building Cost,BI,Notes\n"
        "Plant A,5000000,1000000,Active\n",
        encoding="utf-8",
    )

    result = engine.process(file_path=file_path, job_id="job_ev_006")

    assert len(result.semantic_evidence) == 4

    # Site: ambiguous location_signal
    site_ev = result.semantic_evidence[0]
    assert site_ev.raw_text == "Site"
    assert "location_signal" in site_ev.detected_concepts
    assert site_ev.is_ambiguous is True

    # Building Cost: definitive val_bldg
    bldg_ev = result.semantic_evidence[1]
    assert bldg_ev.raw_text == "Building Cost"
    assert "val_bldg" in bldg_ev.detected_concepts
    assert bldg_ev.is_ambiguous is False


# =====================================================================
# 12 & 23. Actual JSON Serialization & Round-Trip
# =====================================================================


def test_json_serialization_and_round_trip(
    tmp_path: Path, engine: SheetIntelligenceEngine
):
    """Test 12 & 23: Serializes to valid JSON and validates that round-trip structure is identical."""
    file_path = tmp_path / "round_trip.csv"
    file_path.write_text(
        "Ref,Address,City,State,Zip,Building Cost ($),Occupancy\n"
        'R-1,100 Main,Chicago,IL,60601,"$1,500,000",Office\n',
        encoding="utf-8",
    )

    result = engine.process(file_path=file_path, job_id="job_json_007")

    # Serialize using Pydantic JSON method
    json_str = result.model_dump_json(indent=2)
    assert isinstance(json_str, str)

    # Parse back with standard json library
    parsed = json.loads(json_str)

    assert parsed["job_id"] == "job_json_007"
    assert parsed["selected_sheet"] == "default"
    assert parsed["header_row"] == 0
    assert parsed["raw_headers"][5] == "Building Cost ($)"
    assert parsed["sample_rows"][0][5] == "$1,500,000"

    # Re-validate with Pydantic
    re_validated = Agent1HandoffResult.model_validate(parsed)
    assert re_validated == result


# =====================================================================
# 13 & 14. Pydantic Model Validation and Constraints
# =====================================================================


def test_pydantic_validation_rules():
    """Test 13 & 14: Strict Pydantic validation rejects invalid confidence or missing fields."""
    # Confidence > 1.0 must fail
    with pytest.raises(ValidationError):
        Agent1HandoffResult(
            job_id="test",
            source_file="file.xlsx",
            file_type="xlsx",
            confidence=1.5,  # Invalid
        )

    # Confidence < 0.0 must fail
    with pytest.raises(ValidationError):
        Agent1HandoffResult(
            job_id="test",
            source_file="file.xlsx",
            file_type="xlsx",
            confidence=-0.1,  # Invalid
        )

    # Negative total_rows must fail
    with pytest.raises(ValidationError):
        Agent1HandoffResult(
            job_id="test",
            source_file="file.xlsx",
            file_type="xlsx",
            confidence=0.5,
            total_rows=-5,  # Invalid
        )


# =====================================================================
# 15 & 18. Explicit Anti-Mapping Test (Agent 2 Boundary)
# =====================================================================


def test_explicit_anti_mapping_agent_2_boundary(
    tmp_path: Path, engine: SheetIntelligenceEngine
):
    """Test 15 & 18 (CRITICAL): Verify that Agent 1 does NOT produce final canonical mappings.

    Specifically:
    'Site' must NOT become 'address'
    'Location' must NOT become 'reference'
    'Building Cost' must NOT become 'building_value'
    'Value' must NOT become 'building_value'
    """
    file_path = tmp_path / "anti_mapping.csv"
    file_path.write_text(
        "Site,Location,Building Cost,Value\n"
        "Plant 1,Site A,5000000,5000000\n",
        encoding="utf-8",
    )

    result = engine.process(file_path=file_path, job_id="job_boundary_008")
    json_str = result.model_dump_json()
    data = json.loads(json_str)

    # 1. Verify raw headers are preserved verbatim
    assert data["raw_headers"] == ["Site", "Location", "Building Cost", "Value"]

    # 2. Verify NO schema mapping dictionary exists in output
    assert "schema_mapping" not in data
    assert "mapped_fields" not in data
    assert "field_mappings" not in data

    # 3. Verify specific banned mappings do not appear as key-value transformations
    raw_json = json.dumps(data)
    assert '"Site": "address"' not in raw_json
    assert '"Site":"address"' not in raw_json
    assert '"Location": "reference"' not in raw_json
    assert '"Location":"reference"' not in raw_json
    assert '"Building Cost": "building_value"' not in raw_json
    assert '"Building Cost":"building_value"' not in raw_json
